# std lib
import sys
import threading
import subprocess
if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
    import pexpect

# local includes
from client.log.logger import logic_logger


class SessionThread(threading.Thread):
    """
    A SessionThread is responsible of the launching and monitoring
    of the vncviewer in a separate subprocess
    """

    threadscount = 0

    def __init__(self,
                 tunnel_cmd='',
                 vnc_cmd='',
                 passwd='',
                 vncpassword='',
                 otp='',
                 gui_cmd=None,
                 configFile=''):

        self.tunnel_command = tunnel_cmd
        self.vnc_command = vnc_cmd
        self.gui_cmd = gui_cmd
        self.password = passwd
        self.vncpassword = vncpassword
        self.otp = otp
        self.vnc_process = None
        self.tunnel_process = None
        self.configFile = configFile
        threading.Thread.__init__(self)
        self.threadnum = SessionThread.threadscount
        SessionThread.threadscount += 1
        logic_logger.debug('This is thread ' + str(self.threadnum) + ' init.')

    def terminate(self):
        self.gui_cmd = None
        logic_logger.debug('This is thread ' + str(self.threadnum) + ' TERMINATE.')
        if self.vnc_process:
            arguments = 'Args not available on Popen'
            if hasattr(self.vnc_process, 'args'):
                arguments = str(self.vnc_process.args)

            logic_logger.info("Killing vnc process " + str(self.vnc_process.pid) + " args->" + arguments + "<")
            logic_logger.debug("Killing vnc process-->" + str(self.vnc_process.pid))

            self.vnc_process.terminate()
            self.vnc_process = None

        if self.tunnel_process:
            logic_logger.debug("Killing tunnel process-->" + str(self.tunnel_process.pid))
            self.tunnel_process.terminate()
            self.tunnel_process = None

    def run(self):
        logic_logger.debug('This is thread ' + str(self.threadnum) + ' run.')

        if self.gui_cmd:
            self.gui_cmd(active=True)

        if self.configFile:
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
            self.vnc_process=None

        else:
            if sys.platform == 'win32':
                if self.tunnel_command != '':
                    logic_logger.debug('This is thread ' + str(self.threadnum) + "executing-->" +
                                        self.tunnel_command.replace(self.password, "****") + "<--")
                    self.tunnel_process = subprocess.Popen(self.tunnel_command,
                                                           bufsize=1,
                                                           stdout=subprocess.PIPE,
                                                           stderr=subprocess.PIPE,
                                                           stdin=subprocess.PIPE,
                                                           shell=True,
                                                           universal_newlines=True)
                    self.tunnel_process.stdin.close()
                    while True:
                        o = self.tunnel_process.stdout.readline()

                        if o == '' and self.tunnel_process.poll() is not None:
                            continue
                        logic_logger.debug("output from process---->" + o.strip() + "<---")

                        if o.strip() == 'rcm_tunnel':
                            break

                a = self.vnc_command.split("|")

                logic_logger.debug("starting vncviewer-->" +
                                    self.vnc_command.replace(self.password, "****") + "<--")
                logic_logger.debug("splitting-->"+str(a)+"<--")

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
                self.vnc_process = None

            elif sys.platform.startswith('darwin'):
                logic_logger.debug('This is thread ' + str(self.threadnum) +
                                    " executing-->" + self.vnc_command.replace(self.password, "****") + "<--")

                if self.tunnel_command != '':
                    ssh_newkey = 'Are you sure you want to continue connecting'
                    logic_logger.debug('Tunnel commands: ' + str(self.tunnel_command))

                    child = pexpect.spawn(self.tunnel_command,timeout=50)
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

                commandlist=self.vnc_command.split()
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
                self.vnc_process = None

            else:
                # linux
                logic_logger.info('This is thread ' +
                                    str(self.threadnum) +
                                    " executing-->" +
                                    self.vnc_command.replace(self.password, "****") +
                                    "<-vncpass->" + self.vncpassword + "<--")

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

            self.vnc_process = None

            if self.gui_cmd:
                self.gui_cmd(active=False)