# std lib
import threading
import subprocess
import shlex
from sshtunnel import SSHTunnelForwarder

# local includes
from client.miscellaneous.logger import logic_logger
from client.logic.plugin import NativeSSHTunnelForwarder


class SessionThread(threading.Thread):
    """
    A SessionThread is responsible of the launching and monitoring
    of a service in a separate subprocess
    """

    threadscount = 0

    def __init__(self,
                 tunnel_cmd='',
                 service_cmd='',
                 host='',
                 username='',
                 passwd='',
                 gui_cmd=None,
                 configFile='',
                 local_portnumber=0,
                 node='',
                 portnumber=0,
                 tunnelling_method='internal'
                 ):
        self.ssh_server = None
        self.tunnelling_method = tunnelling_method

        self.tunnel_command = tunnel_cmd
        self.service_command = service_cmd
        self.service_process = None

        self.node = node
        self.host = host
        self.username = username
        self.password = passwd
        self.local_portnumber = local_portnumber
        self.portnumber = portnumber

        self.gui_cmd = gui_cmd
        self.configFile = configFile

        threading.Thread.__init__(self)
        self.threadnum = SessionThread.threadscount
        SessionThread.threadscount += 1

        logic_logger.debug('Thread ' + str(self.threadnum) + ' is initialized')

    def terminate(self):
        logic_logger.debug('Killing thread ' + str(self.threadnum))

        # kill the process
        if self.service_process:
            arguments = ''
            if hasattr(self.service_process, 'args'):
                arguments = str(self.service_process.args)

            logic_logger.debug("Killing service process " +
                               str(self.service_process.pid) +
                               " with args " + arguments)

            self.service_process.terminate()

        # stop the tunnelling
        if self.ssh_server:
            self.ssh_server.stop()

        if self.gui_cmd:
            self.gui_cmd(active=False)

    def run(self):
        try:
            logic_logger.debug('Thread ' + str(self.threadnum) + ' is started')

            if self.gui_cmd:
                self.gui_cmd(active=True)

            if self.configFile:
                commandlist = self.service_command.split()
                commandlist.append(self.configFile)
                self.service_process = subprocess.Popen(commandlist,
                                                        bufsize=1,
                                                        stdout=subprocess.PIPE,
                                                        stderr=subprocess.PIPE,
                                                        stdin=subprocess.PIPE,
                                                        shell=False,
                                                        universal_newlines=True)
                self.service_process.wait()
            else:
                if self.tunnelling_method == 'internal':
                    self.execute_service_command_with_internal_ssh_tunnel()
                elif self.tunnelling_method == 'external':
                    self.execute_service_command_with_external_ssh_tunnel()
                else:
                    logic_logger.error(str(self.tunnelling_method) + 'is not a valid option!')

            self.terminate()

        except Exception as e:
            self.terminate()

    def execute_service_command_with_internal_ssh_tunnel(self):

        with SSHTunnelForwarder(
                (self.host, 22),
                ssh_username=self.username,
                ssh_password=self.password,
                remote_bind_address=(self.node, self.portnumber),
                local_bind_address=('127.0.0.1', self.local_portnumber)
        ) as self.ssh_server:

            self.service_process = subprocess.Popen(shlex.split(self.service_command),
                                                    bufsize=1,
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE,
                                                    stdin=subprocess.PIPE,
                                                    shell=False,
                                                    universal_newlines=True)
            self.service_process.stdin.close()
            while self.service_process.poll() is None:
                stdout = self.service_process.stdout.readline()
                if stdout:
                    logic_logger.debug("service process stdout: " + stdout.strip())


    def execute_service_command_with_external_ssh_tunnel(self):

        with NativeSSHTunnelForwarder(
                self.tunnel_command,
                self.password
        ) as self.ssh_server:

            self.service_process = subprocess.Popen(shlex.split(self.service_command),
                                                    bufsize=1,
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE,
                                                    stdin=subprocess.PIPE,
                                                    shell=False,
                                                    universal_newlines=True)
            self.service_process.stdin.close()
            while self.service_process.poll() is None:
                stdout = self.service_process.stdout.readline()
                if stdout:
                    logic_logger.debug("service process stdout: " + stdout.strip())
