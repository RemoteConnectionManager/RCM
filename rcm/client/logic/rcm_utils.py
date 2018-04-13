#!/bin/env python

import os
import string
import random
import threading
import sys
import subprocess

root_rcm_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append( root_rcm_path)

import client.logic.d3des as d3des

import logging
import logging.handlers
module_logger = logging.getLogger('RCM.utils')

if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
    import pexpect

rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)
consoleHandler = logging.StreamHandler()
rootLogger.addHandler(consoleHandler)

exceptionformat=" {1}"
vnc_loglevel=0

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
            if os.path.isfile(exe) and os.access(exe, os.X_OK):
                return exe

    if required:
        tty.die("spack requires '%s'. Make sure it is in your path." % args[0])

    return None


def configure_logging(verbose=0,vnclv=0):

    ### parsing argument
    import argparse
    parser = argparse.ArgumentParser(description='RCM client.')
    parser.add_argument('-d','--debug',default=verbose,type=int,
                   help='define %(prog)s verbosity')
    parser.add_argument('-l','--vncloglev',default=vnclv,type=int,
                   help='pass  this to vnc loglevel')
    p=parser.parse_args()
    verbose=p.debug
#    rootLogger = logging.getLogger()
    global vnc_loglevel
    vnc_loglevel=p.vncloglev
    module_logger.error( "setting verbosity to: "+str(verbose))
    logf=log_folder()
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
    module_logger.error( "log file folder: "+logf)
    consoleFormatter = logging.Formatter('%(threadName)-12.12s: [%(filename)-30.30s %(lineno)-4d]-->%(message)s')
#    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(consoleFormatter)
    if( verbose > 0):
        module_logger.setLevel(logging.DEBUG)
        logging.getLogger('paramiko').setLevel(logging.DEBUG)
        if( verbose > 2):
            logging.getLogger('paramiko.transport').setLevel(logging.DEBUG)
        else:
            logging.getLogger('paramiko.transport').setLevel(logging.INFO)
        rcmLogger=logging.getLogger('RCM')
        rcmLogger.setLevel(logging.DEBUG)
        if( verbose > 2):
            logging.getLogger('RCM.protocol').setLevel(logging.DEBUG)
        else:
            logging.getLogger('RCM.protocol').setLevel(logging.INFO)
        
        rotatehandler = logging.handlers.RotatingFileHandler(
                        os.path.join(log_folder(),'rcm_logfile.txt'), maxBytes=100000, backupCount=5)
        logFormatter = logging.Formatter('%(asctime)s [%(levelname)s:%(name)s] [%(threadName)-12.12s] [%(filename)s:%(funcName)s:%(lineno)d]-->%(message)s')
        rotatehandler.setFormatter(logFormatter)
                
        if( verbose > 2):
            consoleHandler.setLevel(logging.DEBUG)
        else:
            consoleHandler.setLevel(logging.INFO)
        if( verbose > 1):
            consoleHandler.setFormatter(logFormatter)
            
        rootLogger.addHandler(rotatehandler) 
 
        rootLogger.removeHandler(consoleHandler)
        rcmLogger.addHandler(consoleHandler)
        if( verbose > 2): 
            rootLogger.addHandler(consoleHandler)
            rcmLogger.removeHandler(consoleHandler)
        
        exceptionformat="in {0}: {1}\n{2}"
        
    else:
        logging.getLogger('paramiko').setLevel(logging.ERROR)
        logging.getLogger('RCM').setLevel(logging.ERROR)
        
        exceptionformat="in {0}: {1}"


#   rootLogger.addHandler(consoleHandler)

def client_folder():    
    return os.path.join(os.path.expanduser('~'),'.rcm')

def log_folder():    
    return os.path.join(client_folder(),'logs')

def vnc_crypt(vncpass, decrypt=False):
    if(decrypt):
        try:
            if sys.version_info >= (3, 0):
                import binascii
                passpadd = binascii.unhexlify(vncpass)
            else:
                passpadd = vncpass.decode('hex')
        except TypeError as e:
            if e.message == 'Odd-length string':
                module_logger.warning( 'WARN: %s . Chopping last char off... "%s"' % ( e.message, vncpass[:-1] ))
                passpadd = vncpass[:-1].decode('hex')
            else:
                raise
    else:
        passpadd = (vncpass + '\x00'*8)[:8]
        passpadd = passpadd.encode('utf-8')
    strkey = u''.join([ chr(x) for x in d3des.vnckey ])

    if sys.version_info >= (3, 0):
        # python3
        key = d3des.deskey(strkey.encode('utf-8'), decrypt)
        crypted = d3des.desfunc(passpadd, key)
    else:
        key = d3des.deskey(strkey, decrypt)
        crypted = d3des.desfunc(passpadd, key)

    if(decrypt):
        if sys.version_info >= (3, 0):
            import binascii
            hex_crypted = binascii.unhexlify(binascii.hexlify(crypted)).decode('utf-8')
        else:
            hex_crypted = crypted.encode('hex').decode('hex')
        print('crypted hex password-->' + hex_crypted + '<--')
        return hex_crypted
    else:
        if sys.version_info >= (3, 0):
            import binascii
            hex_crypted = binascii.hexlify(crypted).decode('utf-8')
        else:
            # ------------------------------
            hex_crypted = crypted.encode('hex')
        print('crypted hex password-->' + hex_crypted + '<--')
        return hex_crypted


class rcm_cipher():
    def random_pwd_generator(self, size=8, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))


    def __init__ ( self, encryptpass=None ):
        self.encryptpass=encryptpass
        self.vncpassword = self.random_pwd_generator()
        self.acypher=None
        if(self.encryptpass):
            import AESCipher
#           VNC password encription python implementation 
#           from https://github.com/trinitronx/vncpasswd.py
            self.acypher = AESCipher.AESCipher(self.encryptpass)

    def encrypt(self,vncpassword=None):
        if (not vncpassword):
            vncpassword = self.vncpassword
        if(self.acypher):
            return self.acypher.encrypt(vncpassword).decode('utf-8')
        else:
            return vnc_crypt(vncpassword,decrypt=False)

    def decrypt(self,vncpassword):
        if(self.acypher):
            return self.acypher.decrypt(vncpassword).decode('utf-8')
        else:
            return vnc_crypt(vncpassword,decrypt=True)


class pack_info():
    def __init__ ( self):
        if('frozen' in dir(sys)):
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller >= 1.6
                self.basedir = os.path.abspath(sys._MEIPASS)
            elif('_MEIPASS2' in os.environ):
                self.basedir = os.path.abspath(os.environ['_MEIPASS2'])
            else:
                self.basedir = os.path.dirname(os.path.abspath(sys.executable))
                self.debug=False
        else:
            self.basedir = os.path.dirname(os.path.abspath(__file__))
            
        #Read file containing the platform on which the client were build
        buildPlatform = os.path.join(self.basedir,"external","build_platform.txt")
        self.buildPlatformString = ""
        self.rcmVersion = ""
        if (os.path.exists(buildPlatform)):
            in_file = open(buildPlatform,"r")
            self.buildPlatformString = in_file.readline()
            self.rcmVersion = in_file.readline()
            in_file.close()
            

import paramiko
import socket

def get_unused_portnumber():
    sock=socket.socket()
    sock.bind(('',0))
    sn=sock.getsockname()[1]
    sock.close()
    return sn

import queue
threads_exception_queue=queue.Queue()

def get_threads_exceptions():
    go=True
    exc=None
    while go:
        try:
            exc = threads_exception_queue.get(block=False)
        except queue.Empty:
            go=False
        else:
            module_logger.error( "one thread raised ->"+exc)
    if(exc):
        raise Exception("ERROR: "+exc+" in thread")
        
def get_server_command(host,user,passwd=''):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    module_logger.info("getting server command host->"+host+"< user->"+user+"<")
    ssh.connect(host, username=user, password=passwd)
    chan = ssh.get_transport().open_session()
    chan.get_pty()
    stdin = chan.makefile('wb')
    stdout = chan.makefile('rb')

    #stderr = chan.makefile_stderr('rb')
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

    while(loop):
        try:
            # python3
            if sys.version_info >= (3, 0):
                line = str(stdout.readline(), 'utf-8')
            # python2
            else:
                line = stdout.readline()
            module_logger.debug("parsing output line: ->"+line+"<-")
            # print line
            if(end_string in line and start_string in line):
                # print "line-->"+line
                tmp_command = line.split(end_string)[0].split(start_string)[1]
                if(not evn_variable in tmp_command):
                    rcm_server_command=tmp_command
                    loop = False
        # print "rcm_server_command-->"+rcm_server_command+"<--"
            output += line
        except socket.timeout:
            module_logger.warning( "WARNING TIMEOUT: unable to grab output of -->"+get_rcm_server_command+"< on host:"+host)
            loop = False
    # print host,"output-->"+output+"<--"
    # print host,"rcm_server_command-->"+rcm_server_command+"<--"
    return rcm_server_command


class SessionThread( threading.Thread ):

    threadscount = 0

    def __init__ ( self, tunnel_cmd='', vnc_cmd='', passwd = '', vncpassword = '', otp = '', gui_cmd=None, configFile = '', debug = False ):
        self.debug=debug
        self.tunnel_command = tunnel_cmd
        self.vnc_command = vnc_cmd
        self.gui_cmd=gui_cmd
        self.password = passwd
        self.vncpassword = vncpassword
        self.otp = otp
        self.vnc_process = None
        self.tunnel_process = None
        self.configFile = configFile
        threading.Thread.__init__ ( self )
        self.threadnum = SessionThread.threadscount
        SessionThread.threadscount += 1
        if(self.debug): module_logger.debug( 'This is thread ' + str ( self.threadnum ) + ' init.')

    def terminate( self ):
        self.gui_cmd=None
        if(self.debug): module_logger.debug( 'This is thread ' + str ( self.threadnum ) + ' TERMINATE.')
        if(self.vnc_process):
            arguments='Args not available on Popen'
            if(hasattr(self.vnc_process,'args')): arguments=str(self.vnc_process.args) 
            module_logger.info( "Killing vnc process "+ str(self.vnc_process.pid)+" args->"+arguments+"<")
            if(self.debug): module_logger.debug( "Killing vnc process-->"+ str(self.vnc_process.pid))
            self.vnc_process.terminate()
            self.vnc_process=None
        if(self.tunnel_process):
            module_logger.debug("Killing tunnel process-->"+str(self.tunnel_process.pid))
            self.tunnel_process.terminate()
            self.tunnel_process=None

    def run(self):
        if self.debug:
            module_logger.debug('This is thread ' + str(self.threadnum) + ' run.')

        if self.gui_cmd:
            self.gui_cmd(active=True)

        if self.configFile:
            commandlist=self.vnc_command.split()
            commandlist.append(self.configFile)
            if(self.debug):
                module_logger.debug('This is thread ' + str ( self.threadnum ) + ' CONFIGFILE, executing-->'+' '.join(commandlist)+ "<--")
            self.vnc_process=subprocess.Popen(commandlist , bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE,stdin=subprocess.PIPE, shell=False
            )
            self.vnc_process.wait()
            self.vnc_process=None

        else:
            if(sys.platform == 'win32'):

                if(self.tunnel_command != ''):
                    if(self.debug):  module_logger.debug('This is thread ' + str ( self.threadnum ) + "executing-->" + self.tunnel_command.replace(self.password,"****") + "<--")
                    self.tunnel_process=subprocess.Popen(self.tunnel_command , bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE,stdin=subprocess.PIPE, shell=True)
                    self.tunnel_process.stdin.close()
                    while True:
                        o = self.tunnel_process.stdout.readline()
                        #print "into the while!-->",o
                        if o == '' and self.tunnel_process.poll() != None: continue
                        if(self.debug):
                            module_logger.debug( "output from process---->"+o.strip()+"<---" )
                        if o.strip() == 'rcm_tunnel' : break
                a=self.vnc_command.split("|")
                if(self.debug):
                    module_logger.debug( "starting vncviewer-->"+self.vnc_command.replace(self.password,"****")+"<--")
                    module_logger.debug("splitting-->"+str(a)+"<--")
                if(len(a)>1):
                    tmppass=a[0].strip().split()[1].strip()
                    commandlist=a[1].strip()
                else:
                    tmppass=None
                    commandlist=self.vnc_command.split()
                    if(self.debug):
                        module_logger.debug( "vncviewer tmp  pass-->"+tmppass+"<--")
                if(self.debug):
                    module_logger.debug("vncviewer command-->"+str(commandlist)+"<--")

                #self.vnc_process=subprocess.Popen(self.vnc_command , bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE,stdin=subprocess.PIPE, shell=True)
                self.vnc_process=subprocess.Popen(commandlist , bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE,stdin=subprocess.PIPE, shell=False)
                if(tmppass):
                    self.vnc_process.stdin.write(tmppass)
                    o=self.vnc_process.communicate()
                    if(self.debug):
                        module_logger.debug( "vnc res-->"+str(o)+"<--")
                if(self.vnc_process): self.vnc_process.stdin.close()
                if(self.vnc_process): self.vnc_process.wait()
                self.vnc_process=None
            elif ( sys.platform.startswith('darwin')):

                #-#####################   OSX
                if(self.debug): module_logger.debug( 'This is thread ' + str ( self.threadnum ) + " executing-->" + self.vnc_command.replace(self.password,"****") + "<--")
                if (self.tunnel_command != ''):
                    ssh_newkey = 'Are you sure you want to continue connecting'
                    if(self.debug): module_logger.debug( 'Tunnel commands: '+ str( self.tunnel_command))
                    child = pexpect.spawn(self.tunnel_command,timeout=50)
                    i = child.expect([ssh_newkey, 'password:','rcm_tunnel', pexpect.TIMEOUT, pexpect.EOF])
                    
                    if(self.debug): module_logger.info( 'Tunnel return: '+ str( i))
                    if i == 0:
                        #no certificate
                        child.sendline('yes')
                        i = child.expect(['password','standard VNC authentication','rcm_tunnel', pexpect.TIMEOUT, pexpect.EOF])

                    if i == 1:
                        #no certificate
                        child.sendline(self.password)

                    if i == 0 or i == 3:
                        if(self.debug): module_logger.debug( "Timeout connecting to the display.")
                        if(self.gui_cmd): self.gui_cmd(active=False)
                        raise Exception("Timeout connecting to the display.")


                commandlist=self.vnc_command.split()
                self.vnc_process=subprocess.Popen(commandlist , bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE,stdin=subprocess.PIPE, shell=False)
                if(self.vnc_process): self.vnc_process.stdin.close()
                if(self.vnc_process): self.vnc_process.wait()
                self.vnc_process=None

            else:
                # linux
                if self.debug:
                    module_logger.info('This is thread ' +
                                       str(self.threadnum) +
                                       " executing-->" +
                                       self.vnc_command.replace(self.password, "****") +
                                       "<-vncpass->" + self.vncpassword + "<--")

                child = pexpect.spawn(self.vnc_command, timeout=50)
                self.vnc_process = child

                i = child.expect(['continue connecting',
                                  'password',
                                  'standard VNC authentication',
                                  pexpect.TIMEOUT,
                                  pexpect.EOF])

                if i == 0:
                    child.sendline('yes')
                    i = child.expect(['continue connecting',
                                      'password',
                                      'standard VNC authentication',
                                      pexpect.TIMEOUT,
                                      pexpect.EOF])

                if i == 1:
                    child.sendline(self.password)
                    i = child.expect(['continue connecting',
                                      'password',
                                      'standard VNC authentication',
                                      pexpect.TIMEOUT, pexpect.EOF])

                if i == 2:
                    # Standard VNC authentication
                    i = child.expect(['dummy0',
                                      'dummy1',
                                      'Password:',
                                      pexpect.TIMEOUT, pexpect.EOF])
                    child.sendline(self.vncpassword)

                if i == 3 or i == 4:
                    if self.debug:
                        module_logger.error("#REMOVE_FOR_JAVA#Timeout connecting to the display.")

                i = child.expect(['Authentication successful',
                                  pexpect.TIMEOUT,
                                  pexpect.EOF])

                if i > 0:
                    if self.debug:
                        module_logger.error("#REMOVE_FOR_JAVA#Authentication problems.")
                    for line in child:
                        module_logger.debug("#REMOVE_FOR_JAVA#child expect-->" + str(line))

                child.expect(pexpect.EOF, timeout=None)

            self.vnc_process = None

            if self.gui_cmd:
                self.gui_cmd(active=False)


if __name__ == '__main__':

    print (vnc_crypt(vnc_crypt('paperino'),True))
    print (vnc_crypt('paperino',False))

    r=rcm_cipher()
    e=r.encrypt()
    print ("clear-->"+r.decrypt(e)+" crypt->"+e+" recrypt->"+r.encrypt(r.decrypt(e))+" reclear->"+r.decrypt(r.encrypt(r.decrypt(e))))

    ar=rcm_cipher("mypass")
    ae=ar.encrypt()
    print ("stored clear pass-->"+ar.vncpassword+"<--encrypted without par-->"+ae+"<--")
    print ("stored clear pass-->"+ar.vncpassword+"<--decrypt              -->"+ar.decrypt(ae))
    ae=ar.encrypt()
    print ("stored clear pass-->"+ar.vncpassword+"<--enc nopar-->"+ae+"<--")
    print ("stored clear pass-->"+ar.vncpassword+"<--decrypt  -->"+ar.decrypt(ae))
    print ("stored clear pass-->"+ar.vncpassword+"<--recrypt  -->"+ar.encrypt(ar.vncpassword)+"< clear->"+ar.decrypt(ar.encrypt(ar.vncpassword)))
    print ("stored clear pass-->"+ar.vncpassword+"<--recrypt  -->"+ar.encrypt(ar.vncpassword)+"< clear->"+ar.decrypt(ar.encrypt(ar.vncpassword)))
    print ("clear-->"+ar.decrypt(ae)+" crypt->"+ae+" recrypt->"+ar.encrypt(ar.decrypt(ae))+" reclear->"+ar.decrypt(ar.encrypt(ar.decrypt(ae))))


    #print 'om10-->'+get_server_command('om10.eni.cineca.it','cibo19','')+'<--'
    #print 'aux6-->'+get_server_command('aux6.eni.cineca.it','cibo19','')+'<--'
    configure_logging()
    print ('marconi-->'+get_server_command('login.marconi.cineca.it','lcalori0','')+'<--')

