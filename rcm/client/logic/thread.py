# std lib
import os
import sys
import threading
import subprocess
import shlex
from sshtunnel import SSHTunnelForwarder
if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
    import pexpect

# local includes
from client.miscellaneous.logger import logic_logger


class SessionThread(threading.Thread):
    """
    A SessionThread is responsible of the launching and monitoring
    of the vncviewer in a separate subprocess
    """

    threadscount = 0

    def __init__(self,
                 tunnel_cmd='',
                 vnc_cmd='',
                 host='',
                 username='',
                 passwd='',
                 vncpassword='',
                 otp='',
                 gui_cmd=None,
                 configFile='',
                 auth_method='',
                 local_portnumber=0,
                 node='',
                 portnumber=0,
                 tunnelling_method='internal'
                 ):
        self.ssh_server = None
        self.tunnelling_method = tunnelling_method
        self.auth_method = auth_method
        self.tunnel_command = tunnel_cmd
        self.vnc_command = vnc_cmd
        self.host = host
        self.username = username
        self.gui_cmd = gui_cmd
        self.password = passwd
        self.vncpassword = vncpassword
        self.otp = otp
        self.vnc_process = None
        self.tunnel_process = None
        self.configFile = configFile
        self.local_portnumber = local_portnumber
        self.node = node
        self.portnumber = portnumber
        threading.Thread.__init__(self)
        self.threadnum = SessionThread.threadscount
        SessionThread.threadscount += 1
        logic_logger.debug('Thread ' + str(self.threadnum) + ' is initialized')

    def terminate(self):
        self.gui_cmd = None
        logic_logger.debug('Killing thread ' + str(self.threadnum))

        if self.ssh_server:
            self.ssh_server.stop()

        if self.vnc_process:
            arguments = 'Args not available in Popen'
            if hasattr(self.vnc_process, 'args'):
                arguments = str(self.vnc_process.args)

            logic_logger.debug("Killing vnc process " +
                               str(self.vnc_process.pid) +
                               " with args " + arguments)

            self.vnc_process.terminate()

        if self.tunnel_process:
            logic_logger.debug("Killing tunnel process" +
                               str(self.tunnel_process.pid))
            self.tunnel_process.terminate()

    def run(self):
        logic_logger.debug('Thread ' + str(self.threadnum) + ' is started')

        if self.gui_cmd:
            self.gui_cmd(active=True)

        if self.configFile:
            print("CONFIG file branchs")
            commandlist = self.vnc_command.split()
            commandlist.append(self.configFile)
            logic_logger.debug('This is thread ' + str(self.threadnum)
                               + ' CONFIGFILE, executing-->' + ' '.join(commandlist) + "<--")
            self.vnc_process = subprocess.Popen(commandlist,
                                                bufsize=1,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE,
                                                stdin=subprocess.PIPE,
                                                shell=False,
                                                universal_newlines=True)
            self.vnc_process.wait()
        else:
            if self.tunnelling_method == 'internal':
                
                self.execute_vnc_command_with_internal_ssh_tunnel()
            elif self.tunnelling_method == 'external' or self.tunnelling_method == 'via':
                self.execute_vnc_command_with_external_ssh_tunnel()
            else:
                logic_logger.error(str(self.tunnelling_method) + 'is not a valid option!')

        self.vnc_process = None

        if self.gui_cmd:
            self.gui_cmd(active=False)

    def execute_vnc_command_with_internal_ssh_tunnel(self):

        with SSHTunnelForwarder(
                (self.host, 22),
                ssh_username=self.username,
                ssh_password=self.password,
                remote_bind_address=(self.node, self.portnumber),
                local_bind_address=('127.0.0.1', self.local_portnumber)
        ) as self.ssh_server:

            self.vnc_process = subprocess.Popen(shlex.split(self.vnc_command),
                                                bufsize=1,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE,
                                                stdin=subprocess.PIPE,
                                                shell=False,
                                                universal_newlines=True)
            self.vnc_process.stdin.close()
            while self.vnc_process.poll() is None:
                stdout = self.vnc_process.stdout.readline()
                if stdout:
                    logic_logger.debug("output from process: " + stdout.strip())

    def execute_vnc_command_with_external_ssh_tunnel(self):
        if sys.platform == 'win32':
            if self.tunnel_command != '':
                tunnel_command_without_password = self.tunnel_command
                if self.auth_method == 'password':
                    tunnel_command_without_password = self.tunnel_command.replace(self.password, "****")

                logic_logger.debug('Thread ' + str(self.threadnum) + " executing " +
                                   tunnel_command_without_password)
                self.tunnel_process = subprocess.Popen(self.tunnel_command,
                                                       bufsize=1,
                                                       stdout=subprocess.PIPE,
                                                       stderr=subprocess.PIPE,
                                                       stdin=subprocess.PIPE,
                                                       shell=False,
                                                       env=os.environ)
                self.tunnel_process.stdin.close()
                while True:
                    o = self.tunnel_process.stdout.readline()

                    if o == '' and self.tunnel_process.poll() is not None:
                        continue
                    logic_logger.debug("output from process---->" + o.strip() + "<---")

                    if o.strip() == 'rcm_tunnel':
                        break

            a = self.vnc_command.split("|")

            logic_logger.debug("starting vncviewer")
            logic_logger.debug("splitting" + str(a))

            if len(a) > 1:
                tmppass = a[0].strip().split()[1].strip()
                commandlist = a[1].strip()
            else:
                tmppass = None
                commandlist = self.vnc_command.split()

                logic_logger.debug("vncviewer tmp  pass-->" + tmppass + "<--")
                logic_logger.debug("vncviewer command-->" + str(commandlist) + "<--")

            self.vnc_process = subprocess.Popen(commandlist,
                                                bufsize=1,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE,
                                                stdin=subprocess.PIPE,
                                                shell=False,
                                                universal_newlines=True)
            if tmppass:
                self.vnc_process.stdin.write(tmppass)
                o = self.vnc_process.communicate()
                logic_logger.debug("vnc res-->" + str(o) + "<--")

            if self.vnc_process:
                self.vnc_process.stdin.close()
            if self.vnc_process:
                self.vnc_process.wait()

        elif sys.platform.startswith('darwin'):
            if self.tunnel_command != '':
                ssh_newkey = 'Are you sure you want to continue connecting'
                logic_logger.debug('Tunnel commands: ' + str(self.tunnel_command))

                child = pexpect.spawn(self.tunnel_command, timeout=50)
                i = child.expect([ssh_newkey, 'password:', 'rcm_tunnel', pexpect.TIMEOUT, pexpect.EOF])

                logic_logger.info('Tunnel return: ' + str(i))
                if i == 0:
                    # no certificate
                    child.sendline('yes')
                    i = child.expect(['password',
                                      'standard VNC authentication',
                                      'rcm_tunnel',
                                      pexpect.TIMEOUT,
                                      pexpect.EOF])

                if i == 1:
                    # no certificate
                    child.sendline(self.password)

                if i == 0 or i == 3:
                    logic_logger.debug("Timeout connecting to the display.")
                    if self.gui_cmd:
                        self.gui_cmd(active=False)
                    raise Exception("Timeout connecting to the display.")

            commandlist = self.vnc_command.split()
            self.vnc_process = subprocess.Popen(commandlist,
                                                bufsize=1,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE,
                                                stdin=subprocess.PIPE,
                                                shell=False,
                                                universal_newlines=True)
            if self.vnc_process:
                self.vnc_process.stdin.close()
            if self.vnc_process:
                self.vnc_process.wait()

        else:
            # linux
            child = pexpect.spawn(self.vnc_command,
                                  timeout=50)
            self.vnc_process = child

            i = child.expect(['continue connecting',
                              'password',
                              'standard VNC authentication',
                              pexpect.EOF],
                             timeout=None)

            if i == 0:
                child.sendline('yes')
                i = child.expect(['continue connecting',
                                  'password',
                                  'standard VNC authentication',
                                  pexpect.EOF],
                                 timeout=None)

            if i == 1:
                child.sendline(self.password)
                i = child.expect(['continue connecting',
                                  'password',
                                  'standard VNC authentication',
                                  pexpect.EOF],
                                 timeout=None)

            if i == 2:
                # Standard VNC authentication
                i = child.expect(['dummy0',
                                  'dummy1',
                                  'Password:',
                                  pexpect.EOF],
                                 timeout=None)
                child.sendline(self.vncpassword)

            if i == 3 or i == 4:
                logic_logger.debug("#REMOVE_FOR_JAVA#Timeout connecting to the display.")

            i = child.expect(['Authentication successful',
                              pexpect.EOF],
                             timeout=None)

            if i > 0:
                logic_logger.debug("#REMOVE_FOR_JAVA#Authentication problems.")
                for line in child:
                    logic_logger.debug("#REMOVE_FOR_JAVA#child expect-->" + str(line))

            child.expect(pexpect.EOF,
                         timeout=None)
