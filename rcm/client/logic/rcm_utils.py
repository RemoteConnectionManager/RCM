#!/bin/env python

# std lib
import os
import sys
import paramiko
import socket
import queue
import hashlib
import urllib.request
root_rcm_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_rcm_path)

# local includes
from client.miscellaneous.logger import logic_logger
import client.utils.pyinstaller_utils as pyinstaller_utils


exceptionformat = " {1}"
vnc_loglevel = 0


def compute_checksum(filename):
    fh = open(filename, 'rb')
    m = hashlib.md5()
    while True:
        data = fh.read(8192)
        if not data:
            break
        m.update(data)
    return m.hexdigest()


def download_file(url, outfile):
    req_info = urllib.request.urlopen(url)
    file_size = int(req_info.headers['Content-Length'])
    with open(outfile, 'wb') as f:
        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = req_info.read(block_sz)
            if not buffer:
                break
            file_size_dl += len(buffer)
            f.write(buffer)
            p = float(file_size_dl) / file_size


def which(*args, **kwargs):
    """Finds an executable in the path like command-line which.

    If given multiple executables, returns the first one that is found.
    If no executables are found, returns None.

    Parameters:
        *args (str): One or more executables to search for

    Keyword Arguments:
        path (:func:`list` or str): The path to search. Defaults to ``PATH``
        required (bool): If set to True, raise an error if executable not found

    Returns:
        Executable: The first executable that is found in the path
    """
    from six import string_types
    path = kwargs.get('path', os.environ.get('PATH', ''))
    required = kwargs.get('required', False)

    if isinstance(path, string_types):
        path = path.split(os.pathsep)

    for name in args:
        for directory in path:
            exe = os.path.join(directory, name)
            if sys.platform == 'win32':
                exe = exe + '.exe'
                if os.path.isfile(exe):
                    return exe
            else:
                if os.path.isfile(exe) and os.access(exe, os.X_OK):
                    return exe

    return None


def client_folder():
    return os.path.join(os.path.expanduser('~'), '.rcm')


def log_folder():    
    return os.path.join(client_folder(), 'logs')


class pack_info:
    def __init__(self):
        # Read file containing the platform on which the client were build
        build_platform_filename = pyinstaller_utils.resource_path("build_platform.txt")

        self.buildPlatformString = ""
        self.rcmVersion = ""

        if os.path.exists(build_platform_filename):
            logic_logger.debug("Reading build platform file " + build_platform_filename)
            with open(build_platform_filename, "r") as f:
                self.buildPlatformString = f.readline().strip()
                self.rcmVersion = f.readline()
                logic_logger.debug("buildPlatformString=>>" + self.buildPlatformString + "<")
                logic_logger.debug("rcmVersion=>>" + self.rcmVersion + "<")


def get_unused_portnumber():
    sock = socket.socket()
    sock.bind(('', 0))
    sn=sock.getsockname()[1]
    sock.close()
    return sn


threads_exception_queue=queue.Queue()


def get_threads_exceptions():
    go = True
    exc = None
    while go:
        try:
            exc = threads_exception_queue.get(block=False)
        except queue.Empty:
            go = False
        else:
            logic_logger.error("one thread raised ->" + exc)
    if exc:
        raise Exception("ERROR: " + exc + " in thread")


def get_server_command(host, user, passwd=''):
    """
    It call bare ssh server to  check if on login node, the user has defined a variable
    named RCM_SERVER_COMMAND, in tht case the content of that variable overrides the default
    rcm command string used for the remaining part of the server interaction
     """

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    logic_logger.info("getting server command from host " + host + " with user " + user)
    try:
        ssh.connect(host, username=user, password=passwd)
    except Exception as e:
        logic_logger.error("ERROR {0}: ".format(e) + "in ssh.connect to host " + host)
        raise e

    chan = ssh.get_transport().open_session()
    chan.get_pty()
    stdin = chan.makefile('wb')
    stdout = chan.makefile('rb')

    start_string = '_##start##_'
    end_string = '_##end##_'
    evn_variable = '${RCM_SERVER_COMMAND}'
    get_rcm_server_command = 'echo ' + start_string + evn_variable + end_string + '\n'
    chan.invoke_shell()
    chan.sendall(get_rcm_server_command)
    stdin.flush()

    chan.settimeout(20)

    loop = True
    output = ''
    rcm_server_command = ''

    while loop:
        try:
            # python3
            if sys.version_info >= (3, 0):
                line = str(stdout.readline(), 'utf-8')
            # python2
            else:
                line = stdout.readline()
            logic_logger.debug("parsing output line: ->" + line + "<-")

            if end_string in line and start_string in line:
                tmp_command = line.split(end_string)[0].split(start_string)[1]
                if not evn_variable in tmp_command:
                    rcm_server_command=tmp_command
                    loop = False
            output += line
        except socket.timeout:
            logic_logger.warning("WARNING TIMEOUT: unable to grab output of -->" +
                                  get_rcm_server_command + "< on host:" + host)
            loop = False
    return rcm_server_command
