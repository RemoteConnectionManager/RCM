#!/bin/env python
#
# Copyright (c) 2014-2019 CINECA.
#
# This file is part of RCM (Remote Connection Manager) 
# (see http://www.hpc.cineca.it/software/rcm).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

# std lib
import sys
import json
import os
import socket
import traceback

#import paramiko
from sshtunnel import SSHTunnelForwarder
from client.logic.plugin import NativeSSHTunnelForwarder

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

    def __init__(self, plugin_registry=None):
        try:
            self.ssh_command_executor = plugin_registry.get_instance('CommandExecutor')
            self.tunnel_forwarder_class = plugin_registry.plugins['TunnelForwarder'][0]
        except Exception as e:
            logic_logger.error(str(e) + " - " + str(traceback.format_exc()))

        self.user = ''
        self.password = ''
        self.auth_method = ''
        self.preload = ''

        self.subnet = ''
        self.proxynode = ''
        self.commandnode = ''

        self.server_config = None
        self._api_version = None

        # here we instantiate the remote procedure call stub, it will automatically
        # have all the methods of rcm_protocol_server.rcm_protocol class
        self.protocol = rcm_protocol_client.get_protocol()
        self.protocol.decorate = self.prex

        self.session_threads = []
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

        #ssh_executor = plugin.ParamikoSSHCommandExecutor()

        # ssh = paramiko.SSHClient()
        # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # try:
        #     ssh.connect(host, username=self.user, password=self.password, timeout=10)
        #     #self.auth_method = ssh.get_transport().auth_handler.auth_method
        #     stdin, stdout, stderr = ssh.exec_command(fullcommand)
        #     out = ''.join(stdout)
        #     err = stderr.readlines()
        # except Exception as e:
        #     ssh.close()
        #     raise RuntimeError(e)
        # finally:
        #     ssh.close()
        #
        # if err:
        #     logic_logger.warning(err)

        out = self.ssh_command_executor.run_command(host=host, username=self.user, password=self.password, command=fullcommand)
        if out :
            # find where the real server output starts
            index = out.find(rcm.serverOutputString)
            if index != -1:
                index += len(rcm.serverOutputString)
                out = out[index:]
                return out
            else:
                logic_logger.error("Missing serverOutputString: {0} in server output".format(rcm.serverOutputString))
                logic_logger.error(out)



    def list(self):
        # Get the list of sessions for each login node of the cluster
        # and return the merge of all of them

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

    def api_version(self):
        if not self._api_version:
            try:
                self._api_version = self.protocol.version()
            except Exception:
                # if the server fails to send the version,
                # we assume that the api are the oldest (v0.0.1)
                self._api_version = "0.0.1"
            logic_logger.debug("api version: " + str(self._api_version))
        return self._api_version

    def get_config(self):
        o = self.protocol.config(build_platform=json.dumps(rcm_utils.pack_info().to_dict()))
        self.server_config = rcm.rcm_config(o)
        logic_logger.debug("config: " + str(self.server_config))

        if 'jobscript_json_menu' in self.server_config.config:
            logic_logger.debug("jobscript gui json: " + self.server_config.config.get('jobscript_json_menu', ''))

        return self.server_config

    def submit(self, session=None, otp='', gui_cmd=None, configFile=None):
        if not session:
            return

        logic_logger.debug("session: " + str(session.hash))

        compute_node = session.hash['node']
        port_string = session.hash.get('port', '')
        if port_string:
            port_number = int(port_string)
        else:
            port_number = 5900 + int(session.hash['display'])

        login_node = session.hash['nodelogin']
        local_port_number = rcm_utils.get_unused_portnumber()


        plugin_exe = plugin.TurboVNCExecutable()
        plugin_exe.build(session=session, local_portnumber=local_port_number)

        st = thread.SessionThread(plugin_exe.command,
                                  login_node,
                                  self.proxynode,
                                  self.user,
                                  self.password,
                                  gui_cmd,
                                  configFile,
                                  local_port_number,
                                  compute_node,
                                  port_number,
                                  self.tunnel_forwarder_class)

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
