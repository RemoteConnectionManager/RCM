#!/bin/env python

# std lib
import os
import string
import random

import sys
root_rcm_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_rcm_path)

# local includes
# VNC password encription python implementation
# from https://github.com/trinitronx/vncpasswd.py
import client.logic.d3des as d3des
from client.log.logger import logic_logger


exceptionformat = " {1}"
vnc_loglevel = 0


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


def configure_logging(verbose=0, vnclv=0):
    import argparse
    parser = argparse.ArgumentParser(description='RCM client.')
    parser.add_argument('-d',
                        '--debug',
                        default=verbose,
                        type=int,
                        help='define %(prog)s verbosity')
    parser.add_argument('-l',
                        '--vncloglev',
                        default=vnclv,
                        type=int,
                        help='pass  this to vnc loglevel')
    p = parser.parse_known_args()[0]
    verbose = p.debug
    global vnc_loglevel
    vnc_loglevel = p.vncloglev
    logic_logger.error("setting verbosity to: " + str(verbose))
    logf = log_folder()
    try: 
        os.makedirs(logf)
    except OSError:
        if not os.path.isdir(logf):
            raise
    for f in os.listdir(logf):
        print(("deleting "+f))
        file_path = os.path.join(logf, f)
        try: 
            if os.path.isfile(file_path): os.unlink(file_path)
        except OSError:
            print(("failed to remove "+file_path))
    os.chdir(logf)
    logic_logger.error("log file folder: " + logf)
    consoleFormatter = logging.Formatter('%(threadName)-12.12s: [%(filename)-30.30s %(lineno)-4d]-->%(message)s')
    consoleHandler.setFormatter(consoleFormatter)

    if verbose > 0:
        logic_logger.setLevel(logging.DEBUG)
        logging.getLogger('paramiko').setLevel(logging.DEBUG)

        if verbose > 2:
            logging.getLogger('paramiko.transport').setLevel(logging.DEBUG)
        else:
            logging.getLogger('paramiko.transport').setLevel(logging.INFO)

        rcmLogger = logging.getLogger('RCM')
        rcmLogger.setLevel(logging.DEBUG)

        if verbose > 2:
            logging.getLogger('RCM.protocol').setLevel(logging.DEBUG)
        else:
            logging.getLogger('RCM.protocol').setLevel(logging.INFO)
        
        rotatehandler = logging.handlers.RotatingFileHandler(os.path.join(log_folder(), 'rcm_logfile.txt'),
                                                             maxBytes=100000,
                                                             backupCount=5)
        logFormatter = logging.Formatter('%(asctime)s [%(levelname)s:%(name)s] [%(threadName)-12.12s] [%(filename)s:%(funcName)s:%(lineno)d]-->%(message)s')
        rotatehandler.setFormatter(logFormatter)

        if verbose > 2:
            consoleHandler.setLevel(logging.DEBUG)
        else:
            consoleHandler.setLevel(logging.INFO)
        if verbose > 1:
            consoleHandler.setFormatter(logFormatter)
            
        rootLogger.addHandler(rotatehandler) 
 
        rootLogger.removeHandler(consoleHandler)
        rcmLogger.addHandler(consoleHandler)
        if verbose > 2:
            rootLogger.addHandler(consoleHandler)
            rcmLogger.removeHandler(consoleHandler)
        
        exceptionformat = "in {0}: {1}\n{2}"
    else:
        logging.getLogger('paramiko').setLevel(logging.ERROR)
        logging.getLogger('RCM').setLevel(logging.ERROR)
        exceptionformat = "in {0}: {1}"


def client_folder():
    return os.path.join(os.path.expanduser('~'), '.rcm')


def log_folder():    
    return os.path.join(client_folder(), 'logs')


def vnc_crypt(vncpass, decrypt=False):
    if decrypt:
        try:
            if sys.version_info >= (3, 0):
                import binascii
                passpadd = binascii.unhexlify(vncpass)
            else:
                passpadd = vncpass.decode('hex')
        except TypeError as e:
            if e.message == 'Odd-length string':
                logic_logger.warning('WARN: %s . Chopping last char off... "%s"' % (e.message, vncpass[:-1] ))
                passpadd = vncpass[:-1].decode('hex')
            else:
                raise
    else:
        passpadd = (vncpass + '\x00'*8)[:8]
        passpadd = passpadd.encode('utf-8')
    strkey = u''.join([chr(x) for x in d3des.vnckey])

    if sys.version_info >= (3, 0):
        # python3
        key = d3des.deskey(strkey.encode('utf-8'), decrypt)
        crypted = d3des.desfunc(passpadd, key)
    else:
        key = d3des.deskey(strkey, decrypt)
        crypted = d3des.desfunc(passpadd, key)

    if decrypt:
        if sys.version_info >= (3, 0):
            import binascii
            hex_crypted = binascii.unhexlify(binascii.hexlify(crypted)).decode('utf-8')
        else:
            hex_crypted = crypted.encode('hex').decode('hex')
        return hex_crypted
    else:
        if sys.version_info >= (3, 0):
            import binascii
            hex_crypted = binascii.hexlify(crypted).decode('utf-8')
        else:
            hex_crypted = crypted.encode('hex')
        return hex_crypted


class rcm_cipher:
    def random_pwd_generator(self, size=8, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def __init__(self, encryptpass=None):
        self.encryptpass = encryptpass
        self.vncpassword = self.random_pwd_generator()
        self.acypher = None
        if self.encryptpass:
            import client.logic.aes_cipher as aes_cipher
            self.acypher = aes_cipher.AESCipher(self.encryptpass)

    def encrypt(self, vncpassword=None):
        if not vncpassword:
            vncpassword = self.vncpassword
        if self.acypher:
            return self.acypher.encrypt(vncpassword).decode('utf-8')
        else:
            return vnc_crypt(vncpassword, decrypt=False)

    def decrypt(self, vncpassword):
        if self.acypher:
            return self.acypher.decrypt(vncpassword).decode('utf-8')
        else:
            return vnc_crypt(vncpassword, decrypt=True)


class pack_info:
    def __init__(self):
        if 'frozen' in dir(sys):
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller >= 1.6
                self.basedir = os.path.abspath(sys._MEIPASS)
            elif '_MEIPASS2' in os.environ:
                self.basedir = os.path.abspath(os.environ['_MEIPASS2'])
            else:
                self.basedir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            self.basedir = os.path.dirname(os.path.abspath(__file__))

        # Read file containing the platform on which the client were build
        buildPlatform = os.path.join(self.basedir, "external","build_platform.txt")
        self.buildPlatformString = ""
        self.rcmVersion = ""
        if os.path.exists(buildPlatform):
            in_file = open(buildPlatform, "r")
            self.buildPlatformString = in_file.readline()
            self.rcmVersion = in_file.readline()
            in_file.close()


import paramiko
import socket


def get_unused_portnumber():
    sock = socket.socket()
    sock.bind(('', 0))
    sn=sock.getsockname()[1]
    sock.close()
    return sn

import queue
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
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    logic_logger.info("getting server command host->"+host+"< user->"+user+"<")
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


if __name__ == '__main__':

    configure_logging()
    print(vnc_crypt(vnc_crypt('paperino'), True))
    print(vnc_crypt('paperino', False))

    r = rcm_cipher()
    e = r.encrypt()
    print("clear-->" + r.decrypt(e) + " crypt->" + e + " recrypt->" +
          r.encrypt(r.decrypt(e)) + " reclear->" + r.decrypt(r.encrypt(r.decrypt(e))))

    ar = rcm_cipher("mypass")
    ae = ar.encrypt()
    print("stored clear pass-->" + ar.vncpassword + "<--encrypted without par-->" + ae + "<--")
    print("stored clear pass-->" + ar.vncpassword + "<--decrypt              -->" + ar.decrypt(ae))
    ae = ar.encrypt()
    print("stored clear pass-->" + ar.vncpassword + "<--enc nopar-->" + ae + "<--")
    print("stored clear pass-->" + ar.vncpassword + "<--decrypt  -->" + ar.decrypt(ae))
    print("stored clear pass-->" + ar.vncpassword + "<--recrypt  -->" + ar.encrypt(ar.vncpassword)
          + "< clear->" + ar.decrypt(ar.encrypt(ar.vncpassword)))
    print("stored clear pass-->" + ar.vncpassword + "<--recrypt  -->" + ar.encrypt(ar.vncpassword)
          + "< clear->" + ar.decrypt(ar.encrypt(ar.vncpassword)))
    print("clear-->" + ar.decrypt(ae) + " crypt->" + ae + " recrypt->" + ar.encrypt(ar.decrypt(ae))
          + " reclear->" + ar.decrypt(ar.encrypt(ar.decrypt(ae))))

    import argparse
    parser = argparse.ArgumentParser(description='RCM client.')
    parser.add_argument('-t',
                        '--hosts',
                        default=[],
                        nargs='*',
                        help='list of hosts to test')
    parser.add_argument('-u',
                        '--users',
                        default=[os.environ.get('USER')],
                        nargs='*',
                        help='list of users to test')
    p = parser.parse_known_args()
    print(p)
    for host in p[0].hosts:
        for user in p[0].users:
            print("################# " + host + " ############")
            try:
                server_command = get_server_command(host, user, '')
                print(host + ' -->' + server_command + '<--')
            except Exception as e:
                import traceback
                traceback.print_exc()
