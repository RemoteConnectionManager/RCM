#!/bin/env python

# std lib
import sys
import platform
import os 
import getpass
import socket
import paramiko

if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
    import pexpect

# local includes
# in order to parse the pickle message coming from the server, we need to import rcm as below
root_rcm_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_rcm_path)
sys.path.append(os.path.join(root_rcm_path, 'server'))
import rcm
import client.logic.rcm_utils as rcm_utils
import client.logic.rcm_protocol_client as rcm_protocol_client
from client.utils.pyinstaller_utils import resource_path

import logging
module_logger = logging.getLogger('RCM.client')


class rcm_client_connection:

    def __init__(self, proxynode='', user_account='', remoteuser='', password='', pack_info=None):
        self.session_thread = []
        self.debug = True
        self.commandnode = ''
        self.protocol = rcm_protocol_client.get_protocol()

        def mycall(command):
            return self.prex(command)
        self.protocol.mycall = mycall

        if not pack_info:
            self.pack_info = rcm_utils.pack_info()
        else:
            self.pack_info = pack_info

        self.basedir = self.pack_info.basedir
        self.config = dict()
        self.config['ssh'] = dict()
        self.config['vnc'] = dict()
        self.config['ssh']['win32'] = ("PLINK.EXE", " -ssh", "echo yes | ")
        self.config['vnc']['win32'] = ("vncviewer.exe", "")
        self.config['ssh']['linux2'] = ("ssh", "", "")
        self.config['vnc']['linux2'] = ("vncviewer", "")
        # for python3
        self.config['ssh']['linux'] = ("ssh", "", "")
        self.config['vnc']['linux'] = ("vncviewer", "")
        self.config['ssh']['darwin'] = ("ssh", "", "")
        self.config['vnc']['darwin'] = ("vncviewer_java/Contents/MacOS/JavaApplicationStub", "")
        self.config['remote_rcm_server'] = "module load rcm; python $RCM_HOME/bin/server/rcm_new_server.py"

        self.activeConnectionsList = []

        # set the environment
        if getattr(sys, 'frozen', False):
            module_logger.debug("Running in a bundle")
            # if running in a bundle, we hardcode the path
            # of the built-in vnc viewer and plink (windows only)
            os.environ['JAVA_HOME'] = resource_path('turbovnc')
            if sys.platform == 'win32':
                os.environ['PATH'] = os.environ['JAVA_HOME'] + ";" + os.environ['PATH']
                os.environ['PATH'] = resource_path('putty') + ";" + os.environ['PATH']
            else:
                os.environ['PATH'] = os.environ['JAVA_HOME'] + "/bin:" + os.environ['PATH']
            module_logger.debug(os.environ['JAVA_HOME'])
            module_logger.debug(os.environ['PATH'])

        # ssh executable
        if sys.platform == 'win32':
            sshexe = rcm_utils.which('PLINK')
        else:
            sshexe = rcm_utils.which('ssh')
        if not sshexe:
            if sys.platform == 'win32':
                module_logger.error("plink.exe not found! Check the PATH environment variable.")
            else:
                module_logger.error("ssh not found!")
            sys.exit()
        if sys.platform == 'win32':
            # if the executable path contains spaces, it has to be put inside apexes
            sshexe = "\"" + sshexe + "\""
        self.ssh_command = self.config['ssh'][sys.platform][2] + \
                           sshexe + \
                           self.config['ssh'][sys.platform][1]
        module_logger.debug("ssh command: " + self.ssh_command)

        vncexe = rcm_utils.which('vncviewer')
        if not vncexe:
            module_logger.error("vncviewer not found! Check the PATH environment variable.")
            sys.exit()
        if sys.platform == 'win32':
            # if the executable path contains spaces, it has to be put inside apexes
            vncexe = "\"" + vncexe + "\""
        self.vncexe = vncexe
        module_logger.debug("vncviewer path: " + self.vncexe)

    def login_setup(self, host='', remoteuser='', password=None):
        self.proxynode = host

        if remoteuser == '':
            if sys.version_info >= (3, 0):
                self.remoteuser = input("Remote user: ")
            else:
                self.remoteuser = raw_input("Remote user: ")
        else:
            self.remoteuser = remoteuser

        keyfile = os.path.join(self.basedir, 'keys', self.remoteuser + '.ppk')
        if os.path.exists(keyfile):
            if sys.platform == 'win32':
                self.login_options = " -i " + keyfile + " " + self.remoteuser
                
            else:
                module_logger.warning("PASSING PRIVATE KEY FILE NOT IMPLEMENTED ON PLATFORM -->" + sys.platform + "<--")
                self.login_options = " -i " + keyfile + " " + self.remoteuser
                
        else:
            if sys.platform == 'win32':
                if password is None:
                    self.passwd = getpass.getpass("Get password for " + self.remoteuser + "@" + self.proxynode + " : ")
                else:
                    self.passwd = password
                self.login_options = " -pw " + self.passwd + " " + self.remoteuser
            else:
                if password is None:
                    self.passwd = getpass.getpass("Get password for " + self.remoteuser + "@" + self.proxynode + " : ")
                else:
                    self.passwd = password
                self.login_options = self.remoteuser

        self.login_options_withproxy = self.login_options + "@" + self.proxynode
        self.ssh_remote_exec_command = self.ssh_command + " " + self.login_options
        self.ssh_remote_exec_command_withproxy = self.ssh_command + " " + self.login_options_withproxy

        check_cred = self.checkCredential()
        if check_cred:
            self.subnet = '.'.join(socket.gethostbyname(self.proxynode).split('.')[0:-1])
            module_logger.debug("Login host: " + self.proxynode + " subnet: " + self.subnet)
        return check_cred 
        
    def prex(self, cmd, commandnode = ''):
        if self.commandnode == '':
            commandnode = self.proxynode
        else:
            commandnode = self.commandnode
            self.commandnode = ''
        fullcommand = self.ssh_remote_exec_command + "@" + commandnode + ' ' + cmd
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        module_logger.info("on " + commandnode + " run-->" + self.config['remote_rcm_server'] + ' ' + cmd + "<")

        try:
            ssh.connect(commandnode, username=self.remoteuser, password=self.passwd, timeout=10)
        except Exception as e: 
            module_logger.warning("ERROR {0}: ".format(e) + "in ssh.connect to node->" +
                                  commandnode + "< user->" + self.remoteuser + "<")
            return('')

        stdin, stdout, stderr = ssh.exec_command(self.config['remote_rcm_server'] + ' ' + cmd)
        myout = ''.join(stdout)
        myerr = stderr.readlines()
        if myerr:
            module_logger.error(myerr)
            raise Exception("Server error: {0}".format(myerr))

        # find where the real server output starts
        index = myout.find(rcm.serverOutputString)
        if index != -1:
            index += len(rcm.serverOutputString)
            myout = myout[index:]
        return myout

    def list(self):
        # get list of nodes to check of possible sessions
        rcm_utils.get_threads_exceptions()

        o = self.protocol.loginlist(subnet=self.subnet)
        sessions = rcm.rcm_sessions(o)

        a = []
        nodeloginList = []
        proxynode = ''
        state = ''
        for ses in sessions.array:
            proxynode = ses.hash.get('nodelogin', '')
            state = ses.hash.get('state', 'killed')
            if proxynode != '' and not proxynode in nodeloginList and state != 'killed':
                nodeloginList.append(proxynode)
                self.commandnode = proxynode
                o = self.protocol.list(subnet=self.subnet)
                if o:
                    tmp = rcm.rcm_sessions(o)
                    a.extend(tmp.array)
        ret = rcm.rcm_sessions()
        ret.array = a
        return ret

    def newconn(self, queue, geometry, sessionname='', vnc_id='turbovnc_vnc'):
        rcm_cipher = rcm_utils.rcm_cipher()
        vncpassword = rcm_cipher.vncpassword
        vncpassword_crypted = rcm_cipher.encrypt()

        o = self.protocol.new(geometry=geometry,
                              queue=queue,
                              sessionname='\'' + sessionname + '\'',
                              subnet=self.subnet,
                              vncpassword=vncpassword,
                              vncpassword_crypted=vncpassword_crypted,
                              vnc_id=vnc_id)

        session = rcm.rcm_session(o)
        return session 

    def kill(self, session):
        sessionid = session.hash['sessionid']
        nodelogin = session.hash['nodelogin']

        self.commandnode = nodelogin
        o = self.protocol.kill(session_id=sessionid)

    def get_config(self):
        o = self.protocol.config(build_platform=self.pack_info.buildPlatformString)
        self.server_config = rcm.rcm_config(o)
        module_logger.debug("config---->" + str(self.server_config))
        return self.server_config

    def queues(self):
        return self.server_config.config.get('queues', [])

    def vncs(self):
        vncs = self.server_config.config.get('vnc_commands', [])
        return vncs
                
    def vncsession(self, session=None, otp='', gui_cmd=None, configFile=None):
        tunnel_command = ''
        vnc_command = ''
        vncpassword_decrypted = ''

        if session:
            portnumber = 5900 + int(session.hash['display'])
            local_portnumber = rcm_utils.get_unused_portnumber()
            node = session.hash['node']
            nodelogin = session.hash['nodelogin']
            tunnel = session.hash['tunnel']
            vncpassword = session.hash.get('vncpassword', '')

            # Decrypt password
            rcm_cipher = rcm_utils.rcm_cipher()
            vncpassword_decrypted = rcm_cipher.decrypt(vncpassword)

            module_logger.debug("portnumber --> " + str(portnumber) + " node --> " + str(node) + " nodelogin --> "
                                + str(nodelogin) + " tunnel --> " + str(tunnel))

            if sys.platform.startswith('darwin'):
                vnc_command = self.vncexe + " -quality 80 -subsampling 2X" + " -password " + vncpassword_decrypted
                vnc_command += " -loglevel " + str(rcm_utils.vnc_loglevel)
            elif sys.platform == 'win32':
                vnc_command = "echo " + vncpassword_decrypted + " | " + self.vncexe + " -autopass -nounixlogin"
                vnc_command += " -logfile " + os.path.join(rcm_utils.log_folder(), 'vncviewer_' + nodelogin + '_' +
                                                           session.hash.get('sessionid', '') + '.log')
                vnc_command += " -loglevel " + str(rcm_utils.vnc_loglevel)
            else:
                vnc_command = self.vncexe + " -quality 80 " + " -password " + vncpassword_decrypted

            if sys.platform == 'win32' or sys.platform.startswith('darwin'):
                if tunnel == 'y':
                    tunnel_command = self.ssh_command + " -L 127.0.0.1:" + str(local_portnumber) + ":" + node + ":" \
                                     + str(portnumber) + " " + self.login_options + "@" + nodelogin
                    if sys.platform.startswith('darwin'): 
                        tunnel_command += " echo 'rcm_tunnel'; sleep 20"
                    else: 
                        tunnel_command += " echo 'rcm_tunnel'; sleep 10"
                    vnc_command += " 127.0.0.1:" + str(local_portnumber)
                else:
                    vnc_command += " " + nodelogin + ":" + str(portnumber)
            else:
                if tunnel == 'y':
                    vnc_command += " -via '" + self.login_options + "@" + nodelogin + "' " \
                                   + node + ":" + str(session.hash['display'])
                else:
                    vnc_command += ' ' + nodelogin + ":" + session.hash['display']
        else:

            vnc_command = self.vncexe + " -config "

        module_logger.debug("tunnel->" + tunnel_command.replace(self.passwd, "****") +
                            "< vnc->" + vnc_command + "< conffile->" + str(configFile) + "<")

        st = rcm_utils.SessionThread(tunnel_command,
                                     vnc_command,
                                     self.passwd,
                                     vncpassword_decrypted,
                                     otp,
                                     gui_cmd,
                                     configFile,
                                     self.debug)

        module_logger.debug("session  thread--->" + str(st) + "<--- num thread:" + str(len(self.session_thread)))
        self.session_thread.append(st)
        st.start()

    def vncsession_kill(self):
        try:
            module_logger.debug("here in vncsession_kill")
            if self.session_thread:
                for thread in self.session_thread:
                    thread.terminate()
            self.session_thread = None
        except Exception as e:
            module_logger.error(e)

    def __del__(self):
        module_logger.debug("######## destructor")
        self.vncsession_kill()

    def checkCredential(self):
        rcm_server_command = rcm_utils.get_server_command(self.proxynode,
                                                          self.remoteuser,
                                                          passwd=self.passwd)
        if rcm_server_command != '':
            self.config['remote_rcm_server'] = rcm_server_command
        return True


if __name__ == '__main__':
    try:
        rcm_utils.configure_logging()
        print("vncviewer-->"+rcm_utils.which('vncviewer'))
        c = rcm_client_connection()
        host = 'login.marconi.cineca.it'
        c.login_setup(host=host)
        c.debug = False
        print("##########  open sessions on "+host)
        res = c.list()
        res.write(2)
        newc = c.newconn(queue='4core_18_gb_1h_slurm',
                         geometry='1200x1000',
                         sessionname='test',
                         vnc_id='fluxbox_turbovnc_vnc')
        newsession = newc.hash['sessionid']
        print("created session -->", newsession, "<- display->", newc.hash['display'], "<-- node-->", newc.hash['node'])
        c.vncsession(newc)
        res = c.list()
        res.write(2)
        c.kill(newc)
        res = c.list()
        res.write(2)
    except Exception:
        print("ERROR OCCURRED HERE")
        raise
