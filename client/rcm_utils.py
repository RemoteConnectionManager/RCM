#!/bin/env python

import os
import string
import random
import threading
import sys
import subprocess

import AESCipher

#VNC password encription python implementation from https://github.com/trinitronx/vncpasswd.py
import d3des

if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
    import pexpect

def vnc_crypt(vncpass,decrypt=False):
    if(decrypt):
        try:
            passpadd = vncpass.decode('hex')
        except TypeError as e:
            if e.message == 'Odd-length string':
                print 'WARN: %s . Chopping last char off... "%s"' % ( e.message, vncpass[:-1] )
                passpadd = vncpass[:-1].decode('hex')
            else:
                raise
    else:
        passpadd = (vncpass + '\x00'*8)[:8]
    strkey = ''.join([ chr(x) for x in d3des.vnckey ])
    key = d3des.deskey(strkey,decrypt)
    crypted = d3des.desfunc(passpadd, key)
    if(decrypt):
        return crypted.encode('hex').decode('hex')
    else:
        return crypted.encode('hex')


class rcm_cipher():
    def random_pwd_generator(self, size=8, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))


    def __init__ ( self, encryptpass=None ):
        self.encryptpass=encryptpass
        self.vncpassword = self.random_pwd_generator()
        self.acypher=None
        if(self.encryptpass):
            self.acypher = AESCipher.AESCipher(self.encryptpass)

    def encrypt(self,vncpassword=None):
        if (not vncpassword):
            vncpassword = self.vncpassword
        if(self.acypher):
            return self.acypher.encrypt(vncpassword)
        else:
            return vnc_crypt(vncpassword,decrypt=False)

    def decrypt(self,vncpassword):
        if(self.acypher):
            return self.acypher.decrypt(vncpassword)
        else:
            return vnc_crypt(vncpassword,decrypt=True)


class pack_info():
    def __init__ ( self):
        if('frozen' in dir(sys)):
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller >= 1.6
                self.basedir = os.path.abspath(sys._MEIPASS)
            elif(os.environ.has_key('_MEIPASS2')):
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

def get_server_command(host,user,passwd=''):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
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
            line = stdout.readline()
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
            print "WARNING TIMEOUT: unable to grab output of -->"+get_rcm_server_command+"< on host:"+host
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
        if(self.debug): print 'This is thread ' + str ( self.threadnum ) + ' init.'

    def terminate( self ):
        self.gui_cmd=None
        if(self.vnc_process):
            if(self.debug): print "Killing vnc process-->",self.vnc_process
            self.vnc_process.kill()
        if(self.tunnel_process):
            if(self.debug): print "Killing tunnel process-->",self.tunnel_process
            self.tunnel_process.kill()

    def run ( self ):
        if(self.debug):
            print 'This is thread ' + str ( self.threadnum ) + ' run.'
        if(self.gui_cmd): self.gui_cmd(active=True)

        if self.configFile:
            commandlist=self.vnc_command.split()
            commandlist.append(self.configFile)
            self.vnc_process=subprocess.Popen(commandlist , bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE,stdin=subprocess.PIPE, shell=False
            )
            self.vnc_process.wait()
            self.vnc_process=None

        else:
            if(sys.platform == 'win32'):

                if(self.tunnel_command != ''):
                    if(self.debug): print 'This is thread ' + str ( self.threadnum ) + "executing-->" , self.tunnel_command.replace(self.password,"****") , "<--"
                    self.tunnel_process=subprocess.Popen(self.tunnel_command , bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE,stdin=subprocess.PIPE, shell=True)
                    self.tunnel_process.stdin.close()
                    while True:
                        o = self.tunnel_process.stdout.readline()
                        #print "into the while!-->",o
                        if o == '' and self.tunnel_process.poll() != None: continue
                        if(self.debug):
                            print "output from process---->"+o.strip()+"<---"
                        if o.strip() == 'rcm_tunnel' : break
                a=self.vnc_command.split("|")
                if(self.debug):
                    print "starting vncviewer-->"+self.vnc_command.replace(self.password,"****")+"<--"
                    print "splitting-->",a,"<--"
                if(len(a)>1):
                    tmppass=a[0].strip().split()[1].strip()
                    commandlist=a[1].strip()
                else:
                    tmppass=None
                    commandlist=self.vnc_command.split()
                    if(self.debug):
                        print "vncviewer tmp  pass-->",tmppass,"<--"
                if(self.debug):
                    print "vncviewer command-->",commandlist,"<--"

                #self.vnc_process=subprocess.Popen(self.vnc_command , bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE,stdin=subprocess.PIPE, shell=True)
                self.vnc_process=subprocess.Popen(commandlist , bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE,stdin=subprocess.PIPE, shell=False)
                if(tmppass):
                    self.vnc_process.stdin.write(tmppass)
                    o=self.vnc_process.communicate()
                    if(self.debug):
                        print "vnc res-->",o,"<--"
                self.vnc_process.stdin.close()
                self.vnc_process.wait()
                self.vnc_process=None
            elif ( sys.platform.startswith('darwin')):

                #-#####################   OSX
                if(self.debug): print 'This is thread ' + str ( self.threadnum ) + " executing-->" , self.vnc_command.replace(self.password,"****") , "<--"
                if (self.tunnel_command != ''):
                    ssh_newkey = 'Are you sure you want to continue connecting'
                    if(self.debug): print 'Tunnel commands: ', self.tunnel_command
                    child = pexpect.spawn(self.tunnel_command,timeout=50)
                    i = child.expect([ssh_newkey, 'password:', pexpect.TIMEOUT, pexpect.EOF])
                    if i == 0:
                        #no certificate
                        child.sendline('yes')
                        i = child.expect(['password','standard VNC authentication', pexpect.TIMEOUT, pexpect.EOF])

                    if i == 1:
                        #no certificate
                        child.sendline(self.password)

                    if i == 0 or i == 3 or i == 4:
                        if(self.debug): print "Timeout connecting to the display."
                        if(self.gui_cmd): self.gui_cmd(active=False)
                        raise Exception("Timeout connecting to the display.")


                commandlist=self.vnc_command.split()
                self.vnc_process=subprocess.Popen(commandlist , bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE,stdin=subprocess.PIPE, shell=False)
                self.vnc_process.wait()
                self.vnc_process=None

            else:
                #-#####################   linux
                if(self.debug): print 'This is thread ' + str ( self.threadnum ) + " executing-->" , self.vnc_command.replace(self.password,"****") , "<--"

                child = pexpect.spawn(self.vnc_command,timeout=50)
                i = child.expect(['continue connecting', 'password','standard VNC authentication', pexpect.TIMEOUT, pexpect.EOF])

                if i == 0:
                    child.sendline('yes')
                    i = child.expect(['continue connecting', 'password','standard VNC authentication', pexpect.TIMEOUT, pexpect.EOF])

                if i == 1:
                    child.sendline(self.password)
                    i = child.expect(['continue connecting', 'password','standard VNC authentication', pexpect.TIMEOUT, pexpect.EOF])
                if i == 2:
                    # Standard VNC authentication
                    i = child.expect(['dummy0','dummy1','Password:', pexpect.TIMEOUT, pexpect.EOF])
                    child.sendline(self.vncpassword)

                if i == 3 or i == 4:
                    if(self.debug): print "Timeout connecting to the display."
                    if(self.gui_cmd): self.gui_cmd(active=False)
                    raise Exception("Timeout connecting to the display.")
		  
		i = child.expect(['Authentication successful', pexpect.TIMEOUT, pexpect.EOF])
		if i > 0:
                    if(self.debug): print "Authentication problems."
                    if(self.gui_cmd): self.gui_cmd(active=False)
		    for line in child:
		      print "child expect-->",line
                    raise Exception("Authentication problems.")


                child.expect(pexpect.EOF, timeout=None)

            if(self.gui_cmd):
                self.gui_cmd(active=False)


                
                
                
if __name__ == '__main__':

    print vnc_crypt(vnc_crypt('paperino'),True)

    r=rcm_cipher()
    e=r.encrypt()
    print "clear-->"+r.decrypt(e)+" crypt->"+e+" recrypt->"+r.encrypt(r.decrypt(e))+" reclear->"+r.decrypt(r.encrypt(r.decrypt(e)))

    ar=rcm_cipher("mypass")
    ae=ar.encrypt()
    print "stored clear pass-->"+ar.vncpassword+"<--encrypted without par-->"+ae+"<--"
    print "stored clear pass-->"+ar.vncpassword+"<--decrypt              -->"+ar.decrypt(ae)
    ae=ar.encrypt()
    print "stored clear pass-->"+ar.vncpassword+"<--enc nopar-->"+ae+"<--"
    print "stored clear pass-->"+ar.vncpassword+"<--decrypt  -->"+ar.decrypt(ae)
    print "stored clear pass-->"+ar.vncpassword+"<--recrypt  -->"+ar.encrypt(ar.vncpassword)+"< clear->"+ar.decrypt(ar.encrypt(ar.vncpassword))
    print "stored clear pass-->"+ar.vncpassword+"<--recrypt  -->"+ar.encrypt(ar.vncpassword)+"< clear->"+ar.decrypt(ar.encrypt(ar.vncpassword))
    print "clear-->"+ar.decrypt(ae)+" crypt->"+ae+" recrypt->"+ar.encrypt(ar.decrypt(ae))+" reclear->"+ar.decrypt(ar.encrypt(ar.decrypt(ae)))


    print 'om10-->'+get_server_command('om10.eni.cineca.it','cibo19','')+'<--'
    print 'aux6-->'+get_server_command('aux6.eni.cineca.it','cibo19','')+'<--'
    print 'hpc1-->'+get_server_command('login-hpc1.eni.cineca.it','cibo19','')+'<--'