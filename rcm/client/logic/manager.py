#!/bin/env python

# std lib
import sys
import json
import os
import socket
import paramiko

# in order to parse the pickle message coming from the server, we need to import rcm as below
root_rcm_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_rcm_path)
sys.path.append(os.path.join(root_rcm_path, 'server'))

# local includes
import rcm
import client.logic.rcm_utils as rcm_utils
import client.logic.plugin as plugin
import client.logic.cipher as cipher
import client.logic.thread as thread
import client.logic.rcm_protocol_client as rcm_protocol_client
from client.miscellaneous.logger import logic_logger
from client.miscellaneous.config_parser import parser, defaults


class RemoteConnectionManager:
    """
    The remote connection manager is the mediator between the user and the server.
    It allows to login into the server, get the server configuration and
    create/start/kill/list display remote sessions.
    """

    def __init__(self, pack_info=None):
        self.user = ''
        self.password = ''
        self.auth_method = ''

        self.session_threads = []
        self.proxynode = ''
        self.preload = ''
        self.commandnode = ''

        # here we instatiate the remote procedure call stub, it will automatically
        # have all the methods of rcm_protoclo_server.rcm_protocol class
        self.protocol = rcm_protocol_client.get_protocol()

        def mycall(command):
            return self.prex(command)
        self.protocol.mycall = mycall

        if not pack_info:
            self.pack_info = rcm_utils.pack_info()
        else:
            self.pack_info = pack_info

        self.rcm_server_command = json.loads(parser.get('Settings',
                                                        'preload_command',
                                                        fallback=defaults['preload_command']))

    def login_setup(self, host, user, password=None, preload=''):
        self.proxynode = host
        self.preload = preload
        self.user = user
        self.password = password

        self.subnet = '.'.join(socket.gethostbyname(self.proxynode).split('.')[0:-1])
        logic_logger.debug("Login host: " + self.proxynode + " subnet: " + self.subnet)

        return True

    def prex(self, cmd):
        """
        A wrapper around all the remote command execution;
        accept the input command and
        return the remote server output that comes after
        the rcm.serverOutputString separation string
        """
        if self.commandnode == '':
            host = self.proxynode
        else:
            host = self.commandnode
            self.commandnode = ''

        # build the full command
        if self.preload.strip():
            fullcommand = self.preload.strip()

            # if fullcommand ends with ';' add the preset rcm server command, otherwise use it as is
            if fullcommand[-1] == ';':
                fullcommand += ' ' + self.rcm_server_command
        else:
            fullcommand = self.rcm_server_command

        fullcommand += ' ' + cmd
        logic_logger.info("On " + host + " run: <br><span style=\" font-size:5; font-weight:400; color:#101010;\" >" +
                          fullcommand + "</span>")

        # ssh full command execution
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(host, username=self.user, password=self.password, timeout=10)
            self.auth_method = ssh.get_transport().auth_handler.auth_method
            stdin, stdout, stderr = ssh.exec_command(fullcommand)
        except Exception as e:
            ssh.close()
            raise RuntimeError(e)
        finally:
            ssh.close()

        out = ''.join(stdout)
        err = stderr.readlines()
        if err:
            logic_logger.warning("Server report error: {0}".format(err))

        # find where the real server output starts
        index = out.find(rcm.serverOutputString)
        if index != -1:
            index += len(rcm.serverOutputString)
            out = out[index:]
        else:
            logic_logger.error("Missing serverOutputString: {0} in server output".format(rcm.serverOutputString))
            if err:
                raise Exception("Server error: {0}".format(err))

        return out

    def list(self):
        # Get the list of sessions for each login node of the cluster
        # and return the merge of all of them

        rcm_utils.get_threads_exceptions()

        # here we remotely call loginlist function of rcm_protocol_server
        # get from each login nodes to check of possible sessions
        o = self.protocol.loginlist(subnet=self.subnet)
        sessions = rcm.rcm_sessions(o)

        merged_sessions = rcm.rcm_sessions(fromstring='{}')
        nodeloginList = []

        for ses in sessions.get_sessions():
            nodelogin = ses.hash.get('nodelogin', '')
            state = ses.hash.get('state', 'killed')
            if nodelogin != '' and not nodelogin in nodeloginList and state != 'killed':
                nodeloginList.append(nodelogin)
                self.commandnode = nodelogin
                # here we call list of rcm_protocol_server to get the sessions
                o = self.protocol.list(subnet=self.subnet)
                if o:
                    tmp = rcm.rcm_sessions(o)
                    for sess in tmp.get_sessions():
                        merged_sessions.add_session(sess)

        return merged_sessions

    def new(self, queue, geometry, sessionname='', vnc_id='turbovnc_vnc', choices=None):
        rcm_cipher = cipher.RCMCipher()
        vncpassword = rcm_cipher.vncpassword
        vncpassword_crypted = rcm_cipher.encrypt()

        if choices:
            choices_string = json.dumps(choices)
            logic_logger.debug("Newconn protocol choices: " + choices_string)

            o = self.protocol.new(geometry=geometry,
                                  queue=queue,
                                  sessionname='\'' + sessionname + '\'',
                                  subnet=self.subnet,
                                  vncpassword=vncpassword,
                                  vncpassword_crypted=vncpassword_crypted,
                                  vnc_id=vnc_id,
                                  choices_string=choices_string)
        else:
            o = self.protocol.new(geometry=geometry,
                                  queue=queue,
                                  sessionname='\'' + sessionname + '\'',
                                  subnet=self.subnet,
                                  vncpassword=vncpassword,
                                  vncpassword_crypted=vncpassword_crypted,
                                  vnc_id=vnc_id)

        session = rcm.rcm_session(o)
        return session

    def get_config(self):        
        o = self.protocol.config(build_platform=json.dumps(self.pack_info.to_dict()))
        self.server_config = rcm.rcm_config(o)
        logic_logger.debug("config: " + str(self.server_config))
        
        if 'jobscript_json_menu' in self.server_config.config:
            logic_logger.debug("jobscript gui json: " + self.server_config.config.get('jobscript_json_menu', ''))
        
        return self.server_config

    def submit(self, session=None, otp='', gui_cmd=None, configFile=None):
        if not session:
            return

        logic_logger.debug("session: " + str(session.hash))

        portstring = session.hash.get('port', '')
        if portstring:
            portnumber = int(portstring)
        else:
            portnumber = 5900 + int(session.hash['display'])

        local_portnumber = rcm_utils.get_unused_portnumber()
        node = session.hash['node']

        try:
            tunnelling_method = json.loads(parser.get('Settings', 'ssh_client'))
        except Exception:
            tunnelling_method = "internal"
        logic_logger.info("Using " + str(tunnelling_method) + " ssh tunnelling")

        plugin_exe = plugin.TurboVNCExecutable()
        plugin_exe.build(session=session, local_portnumber=local_portnumber)

        ssh_exe = plugin.SSHExecutable()
        ssh_exe.build(self.user, self.password, session, local_portnumber)

        st = thread.SessionThread(ssh_exe.command,
                                  plugin_exe.command,
                                  self.proxynode,
                                  self.user,
                                  self.password,
                                  gui_cmd,
                                  configFile,
                                  local_portnumber,
                                  node,
                                  portnumber,
                                  tunnelling_method)

        logic_logger.debug("session thread: " + str(st) + "; thread number: " + str(len(self.session_threads)))
        self.session_threads.append(st)
        st.start()

    def kill(self, session):
        sessionid = session.hash['sessionid']
        nodelogin = session.hash['nodelogin']

        self.commandnode = nodelogin
        self.protocol.kill(session_id=sessionid)

    def kill_session_thread(self):
        try:
            if self.session_threads:
                for thread in self.session_threads:
                    thread.terminate()
            self.session_threads = None
        except Exception:
            logic_logger.error('Failed to kill a session thread still alive')

