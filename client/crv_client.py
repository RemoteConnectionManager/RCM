#!/bin/env python

import sys
import os 
import getpass
import subprocess
sys.path.append( os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)) ) , "python"))
import crv


class crv_client_connection:

    def __init__(self,proxynode='login2.plx.cineca.it',remoteuser='',password=''):
        self.debug=False
        self.config=dict()
        self.config['ssh']=dict()
        self.config['vnc']=dict()
        self.config['ssh']['win32']=("PLINK.EXE"," -ssh")
        self.config['vnc']['win32']=("vncviewer.exe")
        self.config['remote_crv_server']="/plx/userinternal/cin0118a/remote_viz/crv_server.py"
        self.basedir = os.path.dirname(os.path.abspath(__file__))
        self.sshexe = os.path.join(self.basedir,"external",sys.platform,"bin",self.config['ssh'][sys.platform][0])
        if(self.debug):
            print "uuu", self.sshexe
        if os.path.exists(self.sshexe) :
            self.ssh_command = self.sshexe + self.config['ssh'][sys.platform][1]
        else:
            self.ssh_command = "ssh"
        if(self.debug):
            print "uuu", command
        
        self.vncexe = os.path.join(self.basedir,"external",sys.platform,"bin",self.config['ssh'][sys.platform][0])
        
        self.proxynode=proxynode
        
        if (remoteuser == ''):
            self.remoteuser=raw_input("Remote user: ")

        if (password == ''):
            self.passwd=getpass.getpass("Get password for" + self.remoteuser + "@" + self.proxynode + " : ")
        #    print "got passwd-->",self.passwd

        self.login_options =  " -pw "+self.passwd + " " + self.remoteuser + "@" + self.proxynode
        self.ssh_remote_exec_command = self.ssh_command + self.login_options

    
    def prex(self,cmd):
        fullcommand= self.ssh_remote_exec_command + ' ' + cmd
        if(self.debug):
            print "executing-->",fullcommand
        myprocess=subprocess.Popen(fullcommand, bufsize=100000, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (myout,myerr)=myprocess.communicate()
        if(self.debug):
            print "returned error  -->",myerr
            print "returned output -->",myout
        myprocess.wait()                        
        if(self.debug):
            print "returned        -->",myprocess.returncode
        return (myprocess.returncode,myout,myerr)     

    def list(self):
        (r,o,e)=self.prex(self.config['remote_crv_server'] + ' ' + 'list')
        if (r != 0):
            print e
            raise Exception("Previous command failed (stderr reported above)!")
        sessions=crv.crv_sessions(o)
        if(self.debug):
            sessions.write(2)
        return sessions 
        
    def newconn(self):

        (r,o,e)=self.prex(self.config['remote_crv_server'] + ' ' + 'new')
        
        if (r != 0):
            print e
            raise Exception("Previous command failed (stderr reported above)!")
        session=crv.crv_session(o)
        return session 

    def kill(self,sessionid):

        (r,o,e)=self.prex(self.config['remote_crv_server'] + ' ' + 'kill' + ' ' + sessionid)
        
        if (r != 0):
            print e
            raise Exception("Killling session ->",sessionid,"<- failed ! ")
  
    def vncsession(self,display_num):
        portnumber=5900 + int(display_num)
        print "portnumber-->",portnumber

        tunnel_command=self.sshcommand + " -L " +str(portnumber) + ":"+options.targetnode+":" + str(portnumber) + " " + options.username + "@" + options.proxynode + " cd $HOME; pwd; ls; echo 'pippo'; sleep 10000000"
        print "executing-->" , command , "<--"


if __name__ == '__main__':
    try:
        c = crv_client_connection()
#        c.debug=True
        res=c.list()
        res.write(2)
        newc=c.newconn()
        newsession = newc.hash['sessionid']
        print "created session -->",newsession,"<- display->",newc.hash['display']
        print "created session -->",newsession
        res=c.list()
        res.write(2)
        c.kill(newsession)
        res=c.list()
        res.write(2)
        
        
    except Exception:
        print "ERROR OCCURRED HERE"
        raise
  