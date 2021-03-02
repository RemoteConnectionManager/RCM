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

import sys
import platform
import os
import json
import pexpect
import subprocess
if sys.platform == 'win32':
    from pexpect.popen_spawn import PopenSpawn
    import signal
import threading
import sshtunnel
import paramiko

# local includes
import client.logic.rcm_utils as rcm_utils
from client.miscellaneous.logger import logic_logger
from client.utils.pyinstaller_utils import resource_path
import client.logic.cipher as cipher
from client.miscellaneous.config_parser import parser, defaults

platform_match_table = {'linux2': 'linux'}

class Executable(object):
    """Class representing a program that can be run on the command line."""

    def __init__(self, name):
        self.exe = name.split(' ')
        self.default_env = {}
        self.returncode = None

        # if not self.exe:
        #    raise ProcessError("Cannot construct executable for '%s'" % name)

    def add_default_arg(self, arg):
        """Add a default argument to the command."""
        self.exe.append(arg)

    def add_arg_value(self, arg, value):
        """Add a default argument to the command."""
        self.exe.append(arg)
        self.exe.append(value)

    def add_default_env(self, key, value):
        """Set an environment variable when the command is run.

        Parameters:
            key: The environment variable to set
            value: The value to set it to
        """
        self.default_env[key] = value

    @property
    def command(self):
        """The command-line string.

        Returns:
            str: The executable and default arguments
        """
        return ' '.join(self.exe)

    @property
    def name(self):
        """The executable name.

        Returns:
            str: The basename of the executable
        """
        return os.path.basename(self.path)

    @property
    def path(self):
        """The path to the executable.

        Returns:
            str: The path to the executable
        """
        return self.exe[0]

    @property
    def bundle_path(self):
        if not hasattr(self, 'bundle_prefix'):
            RCM_CI_base_folder = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))))
            self.bundle_prefix = os.path.join(RCM_CI_base_folder,
                                              'external',
                                              'turbovnc_bundle',
                                              platform_match_table.get(sys.platform, sys.platform),
                                              platform.architecture()[0])
        return self.bundle_prefix

class TurboVNCExecutable(Executable):
    def __init__(self):

        self.set_env()

        if sys.platform.startswith('darwin'):
            exe = "open"
        else:
            exe = rcm_utils.which('vncviewer')
            if not exe:
                logic_logger.warning("vncviewer not found in PATH environment variable: " + str(os.environ.get('PATH','')) + " searching local external: " +self.bundle_path )
                exe = rcm_utils.which('vncviewer',path=[os.path.join(self.bundle_path, 'bin')])
                if exe:
                    os.environ['JAVA_HOME'] = self.bundle_path
                    self.set_env()
                else:
                    logic_logger.error("vncviewer not found! " )
            if sys.platform == 'win32':
                # if the executable path contains spaces, it has to be put inside apexes
                exe = "\"" + exe + "\""
            # self.exe = exe
            logic_logger.debug("vncviewer path: " + exe)

        super(TurboVNCExecutable, self).__init__(exe)

    def set_env(self):
        # set the environment
        if getattr(sys, 'frozen', False):
            logic_logger.debug("Running in a bundle")
            # if running in a bundle, we hardcode the path
            # of the built-in vnc viewer and plink (windows only)
            os.environ['JAVA_HOME'] = resource_path('turbovnc')
            if sys.platform == 'win32':
                # on windows 10, administration policies prevent execution  of external programs
                # located in %TEMP% ... it seems that it cannot be loaded

                home_path = os.path.expanduser('~')
                desktop_path = os.path.join(home_path, 'Desktop')
                exe_dir_path = os.path.dirname(sys.executable)
                if os.path.exists(desktop_path):
                    rcm_unprotected_path = os.path.join(exe_dir_path, '.rcm', 'executables')
                    os.makedirs(rcm_unprotected_path, exist_ok=True)
                    dest_dir = os.path.join(rcm_unprotected_path, 'turbovnc')
                    rcm_utils.copytree(resource_path('turbovnc'), dest_dir)
                    os.environ['JAVA_HOME'] = dest_dir
        if os.environ.get('JAVA_HOME',''):
            os.environ['JDK_HOME'] = os.environ['JAVA_HOME']
            os.environ['JRE_HOME'] = os.path.join(os.environ['JAVA_HOME'], 'jre')
            os.environ['CLASSPATH'] = os.path.join(os.environ['JAVA_HOME'], 'lib') + \
                                      os.pathsep + os.path.join(os.environ['JRE_HOME'], 'lib')
            os.environ['PATH'] = os.path.join(os.environ['JAVA_HOME'], 'bin') + os.pathsep + os.environ['PATH']
            logic_logger.debug("JAVA_HOME: " + str(os.environ['JAVA_HOME']))
            logic_logger.debug("JRE_HOME: " + str(os.environ['JRE_HOME']))
            logic_logger.debug("JDK_HOME: " + str(os.environ['JDK_HOME']))
            logic_logger.debug("CLASSPATH: " + str(os.environ['CLASSPATH']))
        logic_logger.debug("PATH: " + str(os.environ['PATH']))

    def build(self, session, local_portnumber):
        nodelogin = session.hash['nodelogin']
        # local_portnumber = rcm_utils.get_unused_portnumber()

        tunnel = session.hash['tunnel']
        try:
            tunnelling_method = json.loads(parser.get('Settings', 'ssh_client'))
        except Exception:
            tunnelling_method = "internal"
        logic_logger.info("Using " + str(tunnelling_method) + " ssh tunnelling")

        # Decrypt password
        vncpassword = session.hash.get('vncpassword', '')
        rcm_cipher = cipher.RCMCipher()
        vncpassword_decrypted = rcm_cipher.decrypt(vncpassword)

        # Darwin
        if sys.platform.startswith('darwin'):
            self.add_arg_value("-W", "vnc://:" + vncpassword_decrypted + "@127.0.0.1:" + str(local_portnumber))

        # Win64
        elif sys.platform == 'win32':
            self.add_default_arg("/nounixlogin")
            self.add_default_arg("/noreconnect")
            self.add_default_arg("/nonewconn")
            self.add_arg_value("/loglevel", "0")
            self.add_arg_value("/password", vncpassword_decrypted)

        # Linux
        else:
            self.add_arg_value("-quality", "80")
            self.add_arg_value("-password", vncpassword_decrypted)
            self.add_default_arg("-noreconnect")
            self.add_default_arg("-nonewconn")

        if not sys.platform.startswith('darwin'):
            if tunnel == 'y':
                self.add_default_arg("127.0.0.1:" + str(local_portnumber))
            else:
                self.add_default_arg(nodelogin + ":" + str(session.hash['display']))

        service_command_without_password = self.command
        if vncpassword_decrypted:
            service_command_without_password = service_command_without_password.replace(vncpassword_decrypted, "***")
        logic_logger.debug("service cmd: " + str(service_command_without_password))


class SSHExecutable(Executable):
    def __init__(self):

        self.set_env()

        # ssh executable
        if sys.platform == 'win32':
            exe = rcm_utils.which('PLINK')
            if not exe:
                logic_logger.warning("PLINK not found in PATH environment variable: " + str(os.environ.get('PATH','')) + " searching local external: " +self.bundle_path )
                exe = rcm_utils.which('PLINK',path=[os.path.join(self.bundle_path, 'bin')])
            print("#############"+exe)
        else:
            exe = rcm_utils.which('ssh')
        if not exe:
            if sys.platform == 'win32':
                logic_logger.error("plink.exe not found! Check the PATH environment variable.")
            else:
                logic_logger.error("ssh not found!")
            return
        if sys.platform == 'win32':
            # if the executable path contains spaces, it has to be put inside apexes
            exe = "\"" + exe + "\""

        super(SSHExecutable, self).__init__(exe)

    def set_env(self):
        return

class SSHTunnelExecutable(SSHExecutable):


    def build(self,
              login_node,
              ssh_username,
              ssh_password,
              remote_bind_address,
              local_bind_address):

        compute_node = str(remote_bind_address[0])
        port_number = str(remote_bind_address[1])

        local_host = str(local_bind_address[0])
        local_port_number = str(local_bind_address[1])

        self.add_default_arg("-N")
        self.add_arg_value("-L", local_host + ":" + local_port_number + ":" + compute_node + ":" + port_number)
        if sys.platform == 'win32':
            self.add_default_arg("-ssh")
            if ssh_password:
                self.add_arg_value("-pw", str(ssh_password))

            default_ssh_pkey = os.path.join(os.path.abspath(os.path.expanduser("~")), '.ssh', 'id_rsa.ppk')
            if os.path.exists(default_ssh_pkey):
                self.add_arg_value("-i", default_ssh_pkey)

        self.add_default_arg(ssh_username + "@" + login_node)

        tunnel_command_without_password = self.command
        if ssh_password:
            tunnel_command_without_password = tunnel_command_without_password.replace(ssh_password, "***")
        logic_logger.debug("tunnel cmd: " + str(tunnel_command_without_password))


class NativeSSHTunnelForwarder(object):
    def __init__(self,
                 ssh_address_or_host=('',22),
                 ssh_config_file=sshtunnel.SSH_CONFIG_FILE,
                 ssh_host_key=None,
                 ssh_password=None,
                 ssh_pkey=None,
                 ssh_private_key_password=None,
                 ssh_proxy=None,
                 ssh_proxy_enabled=True,
                 ssh_username=None,
                 remote_bind_address=None,
                 local_bind_address=None,
                 prompt_handlers=[]):

        ssh_exe = SSHTunnelExecutable()
        ssh_exe.build(login_node=ssh_address_or_host[0],
                      ssh_username=ssh_username,
                      ssh_password=ssh_password,
                      remote_bind_address=remote_bind_address,
                      local_bind_address=local_bind_address)

        self.tunnel_command = ssh_exe.command
        self.tunnel_process = None
        self.password = ssh_password
        self.thread_tunnel = None

        super(NativeSSHTunnelForwarder, self).__init__()

    def __enter__(self):
        if sys.platform == 'win32':
            self.tunnel_process = pexpect.popen_spawn.PopenSpawn(self.tunnel_command)

            i = self.tunnel_process.expect(['connection',
                                            pexpect.TIMEOUT,
                                            pexpect.EOF],
                                           timeout=2)
            if i == 0:
                self.tunnel_process.sendline('yes')

        else:
            self.tunnel_process = pexpect.spawn(self.tunnel_command,
                                                timeout=None)

            i = self.tunnel_process.expect(['continue connecting',
                                            'password',
                                            pexpect.TIMEOUT,
                                            pexpect.EOF],
                                           timeout=2)

            if i == 0:
                self.tunnel_process.sendline('yes')
                logic_logger.debug("accepted host verification")
                i = self.tunnel_process.expect(['continue connecting',
                                                'password',
                                                pexpect.TIMEOUT,
                                                pexpect.EOF],
                                               timeout=2)

            if i == 1:
                self.tunnel_process.sendline(self.password)
                logic_logger.debug("sent password")

            def wait():
                self.tunnel_process.expect(pexpect.EOF)

            self.thread_tunnel = threading.Thread(target=wait)
            self.thread_tunnel.start()

            return self

    def __exit__(self, exc_type, exc_value, tb):
        self.stop()

    def stop(self):
        if self.tunnel_process:
            logic_logger.debug("Stopping ssh tunnelling")
            if sys.platform == 'win32':
                self.tunnel_process.kill(signal.SIGINT)
            else:
                self.tunnel_process.close(force=True)
            self.tunnel_process = None

class WrappedNativeSSHTunnelForwarder():
    def __init__(self, *args, **kwargs):
        pass


class ParamikoCommandExecutor(object):
    def __init__(self,*args, **kwargs):
        self.ssh_connections={}
        super(ParamikoCommandExecutor, self).__init__()

    def _get_connection(self,host='', username='', password=''):
        ssh =  self.ssh_connections.get((host, username), None)
        if ssh :
            if ssh.get_transport() is not None:
                if ssh.get_transport().is_active():
                    return ssh
        else:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh.connect(host, username=username, password=password, timeout=10)
                self.ssh_connections[(host, username)] = ssh
                return ssh
            except Exception as e:
                ssh.close()
                self.ssh_connections[(host, username)] = None
                raise RuntimeError(e)
            ssh.close()
            self.ssh_connections[(host, username)] = None
            return None

    def run_command(self,host='', username='', password='',command=''):
        ssh = self._get_connection(host=host, username=username, password=password)
        if ssh:
            stdin, stdout, stderr = ssh.exec_command(command)
            out = ''.join(stdout)
            err = stderr.readlines()
            if err:
                logic_logger.warning(err)
            return out
        else:
            logic_logger.warning("Unable to get connection to " + username + '@' + host)



class SSHCommandExecutor(object):
    def __init__(self, command_prompt='\[[^\]]*\]\$ ', prompt_handlers=[]):
        self.ssh_connections={}
        self.ssh_exe = SSHExecutable()
        self.command_prompt = command_prompt
        self.prompt_handlers=prompt_handlers
        self.separator_string = r'veryunlikelystring'
        super(SSHCommandExecutor, self).__init__()



    def _get_connection(self,host='', username='', password=''):
        ssh_process =  self.ssh_connections.get((host, username), None)
        if ssh_process :
            if sys.platform != 'win32':
                if ssh_process.isalive():
                    return ssh_process
            else:
                return ssh_process
        else:
            if sys.platform == 'win32':
                print("spawning-->"+self.ssh_exe.command +" " + username + '@' + host+"<---")
                ssh_process = pexpect.popen_spawn.PopenSpawn(self.ssh_exe.command +" " + username + '@' + host,maxread=10000)
                print("@@@@@@@@@@@@@@@spawnwd")
            else:
                ssh_process = pexpect.spawn(self.ssh_exe.command +" " + username + '@' + host, dimensions=(100, 10000))

#            ssh_process = subprocess.Popen(program, stdout=devNull,
#                           stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            expectations=[]
            for (prompt,handler) in self.prompt_handlers:
                expectations.append(prompt)

            expectations = expectations + [self.command_prompt,pexpect.TIMEOUT,pexpect.EOF]
            i = ssh_process.expect(expectations,timeout=4)
            print("SONO qui... tornato: " + str(i))
            while i < len(self.prompt_handlers):
                (prompt,handler) = self.prompt_handlers[i]
                (password, ok) = handler(prompt)
                print("---------received-->"+password+"<@@@@@")
                ssh_process.sendline(password)
                i = ssh_process.expect(expectations, timeout=20)
                print("got i: " + str(i))
            if i == 0:
                logic_logger.info("Host header:" + str(ssh_process.before))
            ssh_process.sendline('#test ' + self.separator_string)
            expectations = [self.separator_string + '(.*?)' + self.command_prompt ,pexpect.TIMEOUT,pexpect.EOF]
            i = ssh_process.expect(expectations,timeout=20)
            if i == 0:
                logic_logger.info("Test ssh execution:" + str(ssh_process.before))
                self.ssh_connections[(host, username)] = ssh_process
                return ssh_process
            else :
                logic_logger.warning("Unable to get connection to " + username + '@' + host + ' pexpect got: ' + str(expectations[i]))
                raise RuntimeError()
            ssh_process.terminate()
            self.ssh_connections[(host, username)] = None
            return None

    def run_command(self,host='', username='', password='',command=''):
        ssh_process = self._get_connection(host=host, username=username, password=password)
        if ssh_process:
            expectations = [self.command_prompt,pexpect.TIMEOUT,pexpect.EOF]
            if sys.platform == 'win32':
#                (rows, cols) = ssh_process.getwinsize()
#                logic_logger.debug("ssh_process win size: " + str((rows, cols)))
                ssh_process.sendline("\r\n")
                i=ssh_process.expect(expectations,timeout=1)
                while i == 0:
                    logic_logger.info("SKIPPING: " + str(expectations[i]) + "<- before ->" + str(ssh_process.before))
                    i=ssh_process.expect(expectations,timeout=1)
                ssh_process.sendline(command+"\r\n")
            
#                i = ssh_process.expect(expectations,timeout=50)
#                if i != 0 :
#                    logic_logger.error("Uneexpected result: " + str(expectations[i]) + "<- before ->" + str(ssh_process.before))
#                    return ''
#                else:
#                    logic_logger.info(
#                        "Ready for command before ##>" + str(ssh_process.before)+"<##")
            else:
                ssh_process.sendline(command)
            logic_logger.debug("@@@sent line##>"+command+"<##")
#            ssh_process.sendline('#' + self.separator_string)
#            expectations = [self.separator_string + '(.*?)' + self.command_prompt,pexpect.TIMEOUT,pexpect.EOF]
            i = ssh_process.expect(expectations,timeout=50)
            if i == 0:
                logic_logger.debug("uuuuuuuuuuuu@@@received line##>"+str(ssh_process.before)+"<##")
                cleaned_out=''
                for line in ssh_process.before.splitlines():
                    logic_logger.debug("@@@received line##@"+str(line)+"@##")
                    cleaned_out = cleaned_out + (line + str.encode('\n')).decode()
#                out = ssh_process.before
                return cleaned_out
            else:
                logic_logger.warning("Uneexpected result: " + str(expectations[i].__name__) + "<- before ->" + str(ssh_process.before))

        else:
            logic_logger.warning("Unable to get connection to " + username + '@' + host)



class PluginRegistry():
    def __init__(self):
        self.plugins={}

        ssh_method_selector={'internal': (sshtunnel.SSHTunnelForwarder,ParamikoCommandExecutor),
                             'external': (NativeSSHTunnelForwarder,SSHCommandExecutor) }
        try:
            (tunnel_forwarder_class, command_executor_class) = ssh_method_selector[json.loads(parser.get('Settings', 'ssh_client'))]
        except Exception:
            (tunnel_forwarder_class, command_executor_class) = ssh_method_selector["internal"]
            logic_logger.warning("invalid ssh_client setting, resort to internal" )

        self.plugins['TunnelForwarder'] = [tunnel_forwarder_class, {}, None]
        self.plugins['CommandExecutor'] = [command_executor_class, {}, None]
        message=''
        for plug_type in self.plugins:
            message += plug_type + ": " + str(self.plugins[plug_type][0].__module__) + '.' + str(self.plugins[plug_type][0].__name__)
        logic_logger.info(message)

    def CommandExecutor(self):
        if not 'CommandExecutor' in self.plugin_dict:
            self.plugin_dict['CommandExecutor'] = ParamikoCommandExecutor()
        return self.plugin_dict['CommandExecutor']

    def register_plugins_params(self,name,params={}):
        if name in self.plugins:
            self.plugins[name][1] = params
        else:
            logic_logger.warning("Invalid plugin name: >" + name + "< registering params")

    def get_instance(self, name):
        if name in self.plugins:
            if None == self.plugins[name][2]:
                logic_logger.debug("Istanciating plugin : >" + name + "< class: " +
                                   str(self.plugins[name][0].__module__) + '.' + str(self.plugins[name][0].__name__) +
                                   "params: >" + str(self.plugins[name][1]) + "<:::::")
                self.plugins[name][2] = self.plugins[name][0](**self.plugins[name][1])
            return self.plugins[name][2]
        else:
            logic_logger.error("Invalid plugin name: >" + name + "< asking plugin instance")


