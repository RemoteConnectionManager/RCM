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

# local includes
from client.miscellaneous.logger import logic_logger
import client.logic.plugin as plugin


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
                 tunnelling_plugin=None
                 ):
        self.ssh_server = None

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
        self.tunnelling_plugin = tunnelling_plugin

        threading.Thread.__init__(self)
        self.threadnum = SessionThread.threadscount
        SessionThread.threadscount += 1

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




    def execute_service_command_with_ssh_tunnel(self):
        default_ssh_pkey = os.path.join(os.path.abspath(os.path.expanduser("~")), '.ssh', 'id_rsa')
        additional_params = {'ssh_address_or_host':(self.host, 22),
                             'ssh_username' : self.username,
                             'ssh_password' : self.password,
                             'ssh_pkey' : default_ssh_pkey,
                             'remote_bind_address' : (self.node, self.portnumber),
                             'local_bind_address' : ('127.0.0.1', self.local_portnumber)
                             }
        with plugin.get_plugin_instance(self.tunnelling_plugin, additional_params=additional_params, reuse_instance=False) as self.ssh_server:
        # with self.tunnelling_class(
        #         (self.host, 22),
        #         ssh_username=self.username,
        #         ssh_password=self.password,
        #         ssh_pkey=default_ssh_pkey,
        #         remote_bind_address=(self.node, self.portnumber),
        #         local_bind_address=('127.0.0.1', self.local_portnumber)
        # ) as self.ssh_server:
            arguments = shlex.split(self.service_command)
            if '"\\' == self.service_command[0:2]:
                arguments=['\\'+arguments[0]]+arguments[1:]
            logic_logger.debug("running service command: " + self.service_command)
            logic_logger.debug("shlex: " + str(shlex.split(self.service_command)))
            print("shlex-->"+shlex.split(self.service_command)[0]+"<--")
            self.service_process = subprocess.Popen(arguments,
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


    def run(self):
        try:
            logic_logger.debug('Thread ' + str(self.threadnum) + ' is started')

            if self.gui_cmd:
                self.gui_cmd(active=True)

            self.execute_service_command_with_ssh_tunnel()
            self.terminate()

        except Exception as e:
            self.terminate()
            logic_logger.error("Error on service command\n" +
                               self.service_command +
                               "\n Error:" + str(e) + " ---------------\n " + str(traceback.format_exc()) + '\n-------------')
