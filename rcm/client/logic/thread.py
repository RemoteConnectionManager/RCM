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

import threading
import subprocess
import traceback
import shlex
from sshtunnel import SSHTunnelForwarder
import os
import sys

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
                 service_cmd='',
                 login_node='',
                 host='',
                 username='',
                 passwd='',
                 gui_cmd=None,
                 configFile='',
                 local_port_number=0,
                 compute_node='',
                 port_number=0,
                 tunnelling_method='internal'
                 ):
        self.ssh_server = None
        self.tunnelling_method = tunnelling_method

        self.service_command = service_cmd
        self.service_process = None

        self.login_node = login_node
        self.node = compute_node
        self.host = host # proxynode
        self.username = username
        self.password = passwd
        self.local_portnumber = local_port_number
        self.portnumber = port_number

        self.gui_cmd = gui_cmd
        self.configFile = configFile

        threading.Thread.__init__(self)
        self.threadnum = SessionThread.threadscount
        SessionThread.threadscount += 1

        self.startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.startupinfo = startupinfo

        logic_logger.debug('Thread ' + str(self.threadnum) + ' is initialized')

    def terminate(self):
        logic_logger.debug('Killing thread ' + str(self.threadnum))

        # kill the process
        if self.service_process:
            logic_logger.debug("Killing service process " +
                               str(self.service_process.pid))
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
                                                        universal_newlines=True,
                                                        startupinfo=self.startupinfo,
                                                        )
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
            logic_logger.error("Error running service command\n-->" +
                               self.service_command +
                               "<--\n Error:" + str(e) + " ---- " + str(traceback.format_exc()))

    def execute_service_command_with_internal_ssh_tunnel(self):
        default_ssh_pkey = os.path.join(os.path.abspath(os.path.expanduser("~")), '.ssh', 'id_rsa')
        with SSHTunnelForwarder(
                (self.host, 22),
                ssh_username=self.username,
                ssh_password=self.password,
                ssh_pkey=default_ssh_pkey,
                remote_bind_address=(self.node, self.portnumber),
                local_bind_address=('127.0.0.1', self.local_portnumber)
        ) as self.ssh_server:
            self.service_process = subprocess.Popen(shlex.split(self.service_command),
                                                    bufsize=1,
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE,
                                                    stdin=subprocess.PIPE,
                                                    shell=False,
                                                    universal_newlines=True,
                                                    startupinfo=self.startupinfo,
                                                    )
            self.service_process.stdin.close()
            while self.service_process.poll() is None:
                stdout = self.service_process.stdout.readline()
                if stdout:
                    logic_logger.debug("service process stdout: " + stdout.strip())


    def execute_service_command_with_external_ssh_tunnel(self):

        with NativeSSHTunnelForwarder(
                login_node=self.login_node,
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
                                                    universal_newlines=True,
                                                    startupinfo=self.startupinfo,
                                                    )
            self.service_process.stdin.close()
            while self.service_process.poll() is None:
                stdout = self.service_process.stdout.readline()
                if stdout:
                    logic_logger.debug("service process stdout: " + stdout.strip())
