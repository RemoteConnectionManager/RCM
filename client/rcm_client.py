#!/bin/env python

import sys
import platform
import os 
import getpass
import socket
import time
import paramiko
import string





if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
    import pexpect


sys.path.append( os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)) ) , "server"))
import rcm
import rcm_utils
import rcm_protocol_client

import logging
module_logger = logging.getLogger('RCM.client')


class rcm_client_connection:

    def __init__(self,proxynode='login.plx.cineca.it', user_account='', remoteuser='',password='', pack_info=None):
        self.debug=True
        self.commandnode=''
        self.protocol=rcm_protocol_client.get_protocol()
        def mycall(command):
            return self.prex(command)
        self.protocol.mycall=mycall

        if(not pack_info):
            self.pack_info=rcm_utils.pack_info()
        else:
            self.pack_info=pack_info 
        self.basedir = self.pack_info.basedir
        self.config=dict()
        self.config['ssh']=dict()
        self.config['vnc']=dict()
        self.config['ssh']['win32']=("PLINK.EXE"," -ssh","echo yes | ")
        self.config['vnc']['win32']=("vncviewer.exe","")
        self.config['ssh']['linux2']=("ssh","","")
        self.config['vnc']['linux2']=("vncviewer","")
        self.config['ssh']['darwin']=("ssh","","")
        self.config['vnc']['darwin']=("vncviewer_java/Contents/MacOS/JavaApplicationStub","")

        self.config['remote_rcm_server']="module load rcm; python $RCM_HOME/bin/server/rcm_new_server.py"
        #self.config['remote_rcm_server']="module load python; /om/home/cibo19/RCM_Dev/bin/server/rcm_server.py"
        #finding out the basedir, it depends if we are running as executable pyinstaler or as script
        self.sshexe = os.path.join(self.basedir,"external",sys.platform,platform.architecture()[0],"bin",self.config['ssh'][sys.platform][0])
        self.activeConnectionsList = []
        if os.path.exists(self.sshexe) :
            self.ssh_command = self.config['ssh'][sys.platform][2] + self.sshexe + self.config['ssh'][sys.platform][1]
        else:
            self.ssh_command = "ssh"
        if(self.debug):
             module_logger.debug( "ssh command1: "+ self.ssh_command)
        
        vncexe = os.path.join(self.basedir,"external",sys.platform,platform.architecture()[0],"bin",self.config['vnc'][sys.platform][0])
        if os.path.exists(vncexe):
            self.vncexe=vncexe
        else:
            if(self.debug): 
                module_logger.debug( "VNC exec -->"+vncexe+"<-- NOT FOUND !!!")
                name=raw_input("VNC exec -->"+vncexe+"<-- NOT FOUND !!!")
            sys.exit()
        self.session_thread=[]


    def login_setup(self, host='', remoteuser='',password=''):
        self.proxynode=host
           
        
        if (remoteuser == ''):
            self.remoteuser=raw_input("Remote user: ")
        else:
            self.remoteuser=remoteuser
        keyfile=os.path.join(self.basedir,'keys',self.remoteuser+'.ppk')
        if(os.path.exists(keyfile)):
            if(sys.platform == 'win32'):
                self.login_options =  " -i " + keyfile + " " + self.remoteuser               
                
            else:
                if(self.debug): module_logger.warning( "PASSING PRIVATE KEY FILE NOT IMPLEMENTED ON PLATFORM -->"+sys.platform+"<--")
                self.login_options =  " -i " + keyfile + " " + self.remoteuser
                
        else:
            if(sys.platform == 'win32'):
                if (password == ''):
                    self.passwd=getpass.getpass("Get password for " + self.remoteuser + "@" + self.proxynode + " : ")
                #    print "got passwd-->",self.passwd
                else:
                    self.passwd=password
                self.login_options =  " -pw "+self.passwd + " " + self.remoteuser

            else:
                if (password == ''):
                    self.passwd=getpass.getpass("Get password for " + self.remoteuser + "@" + self.proxynode + " : ")
                    
                #    print "got passwd-->",self.passwd
                else:
                    self.passwd=password
                    self.login_options =  self.remoteuser
        
        self.login_options_withproxy =  self.login_options + "@" + self.proxynode
        self.ssh_remote_exec_command = self.ssh_command + " " + self.login_options
        self.ssh_remote_exec_command_withproxy = self.ssh_command + " " + self.login_options_withproxy 
        check_cred=self.checkCredential()
        if(check_cred):
            self.subnet= '.'.join(socket.gethostbyname(self.proxynode).split('.')[0:-1])
            if(self.debug): module_logger.debug( "Login host: " + self.proxynode + " subnet: " + self.subnet)
        return check_cred 
        
    def prex(self, cmd, commandnode = ''):
        
#        if (commandnode == ''):
        if (self.commandnode == ''):
            commandnode = self.proxynode
        else:
            commandnode = self.commandnode
            self.commandnode=''
        fullcommand = self.ssh_remote_exec_command + "@" + commandnode + ' ' + cmd
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        module_logger.info( "on "+commandnode+" run-->"+self.config['remote_rcm_server'] + ' '+cmd+"<")

        
        try:
            ssh.connect(commandnode, username=self.remoteuser, password=self.passwd, timeout=10)
        except Exception as e: 
            module_logger.warning("ERROR {0}: ".format( e)+"in ssh.connect to node->"+ commandnode +"< user->"+self.remoteuser+"<" )  
            return('') 
        stdin, stdout, stderr = ssh.exec_command(self.config['remote_rcm_server'] + ' ' +cmd)
        myout = ''.join(stdout)
        myerr = stderr.readlines()
        if myerr:
            if(self.debug): module_logger.error( myerr )
            raise Exception("Server error: {0}".format(myerr))

        #find where the real server output starts
        #serverOutputString = "server output->"
        index = myout.find(rcm.serverOutputString)
        if  index != -1:
            index += len(rcm.serverOutputString)
            myout = myout[index:]
            #########myout = myout.replace('\n', '',1)
        return myout
        

    def list(self):
        #get list of nodes to check of possible sessions
        rcm_utils.get_threads_exceptions()
        
        o=self.protocol.loginlist(subnet=self.subnet)
        sessions=rcm.rcm_sessions(o)
        #if(self.debug): 
        #    sessions.write(2)

        a=[]
        nodeloginList = []
        proxynode = ''
        state = ''
        for ses in sessions.array:
            proxynode = ses.hash.get('nodelogin', '')
            state = ses.hash.get('state', 'killed')
            if (proxynode != '' and not proxynode in nodeloginList and state != 'killed'):
                nodeloginList.append(proxynode)
#                (o,e)=self.prex(self.config['remote_rcm_server'] + ' ' + 'list' + ' ' + self.subnet, proxynode)
                self.commandnode=proxynode
                o=self.protocol.list(subnet=self.subnet)
                if(o):
                    tmp=rcm.rcm_sessions(o)
                    a.extend(tmp.array)
        ret=rcm.rcm_sessions()
        ret.array=a
        #if(self.debug):
        #    ret.write(2)
        return ret
        

    def newconn(self, queue, geometry, sessionname = '',vnc_id='turbovnc_vnc'):
        
        #Create a random vncpassword and encrypt it
        rcm_cipher = rcm_utils.rcm_cipher()
        vncpassword = rcm_cipher.vncpassword
        vncpassword_crypted=rcm_cipher.encrypt()
        
        #new_encoded_param='geometry='+ geometry + ' ' + 'queue='+ queue + ' ' +  'sessionname=' + '\'' + sessionname + '\'' + ' ' \
        # + 'subnet=' + self.subnet + ' ' + 'vncpassword=' + vncpassword + ' ' + 'vncpassword_crypted=' + '\'' + vncpassword_crypted + '\''
        #o=self.prex('new' + ' ' + new_encoded_param )

        o=self.protocol.new(geometry=geometry, queue=queue, sessionname='\'' + sessionname + '\'', subnet=self.subnet, vncpassword=vncpassword,
        vncpassword_crypted=vncpassword_crypted, vnc_id=vnc_id)
        
        session=rcm.rcm_session(o)
        return session 

    def kill(self,session):
        sessionid = session.hash['sessionid']
        nodelogin = session.hash['nodelogin']

        self.commandnode=nodelogin
        o=self.protocol.kill(session_id=sessionid)
        

  
#    def get_otp(self,sessionid):
#        (o,e)=self.prex(self.config['remote_rcm_server'] + ' ' + 'otp' + ' ' + sessionid)

#        if e:
#            if(self.debug): print e
#            raise Exception("Getting OTP passwd session -> {0} <- failed with error: {1}".format(sessionid, e))
#            return ''
#        else:
#            return o.strip()

    def get_config(self):
#        o=self.prex('version' + ' ' + self.pack_info.buildPlatformString)
        o=self.protocol.config(build_platform=self.pack_info.buildPlatformString)
        self.server_config=rcm.rcm_config(o)
        module_logger.debug( "config---->"+ str(self.server_config))
        return self.server_config

    def queues(self):
        return self.server_config.config.get('queues',[])

    def vncs(self):
        vncs=self.server_config.config.get('vnc_commands',[])
        return vncs

    #def get_version(self):
#        o=self.prex('version' + ' ' + self.pack_info.buildPlatformString)
        #def mycall(command):
        #    return self.prex(command)
        #protocol=rcm.rcm_protocol(mycall)
        #o=protocol.version(self.pack_info.buildPlatformString)
        #return o.split(' ')


#removed    def get_queue(self):
#        o=self.prex('queue')

#removed        o=self.protocol.queue()

#removed        if(self.debug): print "available queue: ", o
#removed        return o.split(' ')

                
    def vncsession(self, session=None, otp='', gui_cmd=None, configFile=None):
        """

        :rtype : object
        """
        tunnel_command = ''
        vnc_command = ''
        vncpassword_decrypted = ''

        if session:

            portnumber = 5900 + int(session.hash['display'])
            local_portnumber=rcm_utils.get_unused_portnumber()
            node = session.hash['node']
            nodelogin = session.hash['nodelogin']
            tunnel = session.hash['tunnel']
            vncpassword = session.hash.get('vncpassword','')

            #Decrypt password
            rcm_cipher = rcm_utils.rcm_cipher()
            vncpassword_decrypted=rcm_cipher.decrypt(vncpassword)

            if(self.debug):
                module_logger.debug( "portnumber --> "+ str(portnumber) +" node --> " + str(node) + " nodelogin --> " + str(nodelogin)+ " tunnel --> "+str(tunnel))


            if sys.platform.startswith('darwin') :
                vnc_command = self.vncexe + " -quality 80 -subsampling 2X" + " -password " + vncpassword_decrypted
                vnc_command += " -loglevel "+str(rcm_utils.vnc_loglevel)
            elif(sys.platform == 'win32'):
            #    vnc_command = self.vncexe + " -medqual " + "-password " + vncpassword_decrypted
                vnc_command = "echo "+ vncpassword_decrypted+ " | " + self.vncexe + " -medqual " + "-autopass -nounixlogin"
                vnc_command += " -logfile "+os.path.join(rcm_utils.log_folder(),'vncviewer_'+nodelogin+'_'+session.hash.get('sessionid','')+'.log')
                vnc_command += " -loglevel "+str(rcm_utils.vnc_loglevel)
            else:
                vnc_command = self.vncexe + " -medqual "
                #vnc_command += " -logfile "+os.path.join(rcm_utils.log_folder(),'vncviewer_'+nodelogin+'_'+session.hash.get('sessionid','')+'.log')



            if(sys.platform == 'win32' or sys.platform.startswith('darwin')):
                if (tunnel == 'y'):
                    tunnel_command = self.ssh_command  + " -L 127.0.0.1:" +str(local_portnumber) + ":" + node + ":" + str(portnumber) + " " + self.login_options + "@" + nodelogin 
                    if sys.platform.startswith('darwin'): 
                        tunnel_command +=  " echo 'rcm_tunnel'; sleep 20"
                    else: 
                        tunnel_command +=  " echo 'rcm_tunnel'; sleep 10"
                    vnc_command += " 127.0.0.1:" + str(local_portnumber)
                else:
                    #tunnel_command = self.ssh_command  + " -L 127.0.0.1:" +str(portnumber) + ":" + node + ":" + str(portnumber) + " " + self.login_options + "@" + nodelogin + " echo 'rcm_tunnel'; sleep 10"
                    vnc_command += " " + nodelogin + ":" + str(portnumber)
            else:
                if (tunnel == 'y'):
                    vnc_command += " -via '"  + self.login_options + "@" + nodelogin + "' " + node +":" + str(session.hash['display'])
                else:
                    vnc_command += ' ' + nodelogin + ":" + session.hash['display']
        else:

            vnc_command = self.vncexe + " -config "

                
        
        if(self.debug): module_logger.info( "tunnel->"+tunnel_command.replace(self.passwd,"****")+"< vnc->"+vnc_command+"< conffile->"+str(configFile)+"<")

        st=rcm_utils.SessionThread ( tunnel_command, vnc_command, self.passwd, vncpassword_decrypted,  otp, gui_cmd, configFile, self.debug)

        if(self.debug): module_logger.debug( "!!!!!session  thread--->"+str(st)+"<- num thread:"+str(len(self.session_thread)))
        self.session_thread.append(st)
        st.start()

    def vncsession_kill(self):
        if(self.debug): module_logger.debug( "here in vncsession_kill")
        for t in self.session_thread:
            t.terminate()
            
    def checkCredential(self):
        
        #check if RCM_PATH env variable is set
        #try:
            rcm_server_command=rcm_utils.get_server_command(self.proxynode, self.remoteuser, passwd=self.passwd)
            if(rcm_server_command != '' ):
                    self.config['remote_rcm_server'] = rcm_server_command
            return True
        #except Exception as e:
            #if(self.debug): print ""

        #return True


    
if __name__ == '__main__':
    try:
        
        c = rcm_client_connection()
        c.login_setup()
        c.debug=False
        res=c.list()
        res.write(2)
        newc=c.newconn()
        newsession = newc.hash['sessionid']
        print "created session -->",newsession,"<- display->",newc.hash['display'],"<-- node-->",newc.hash['node']
        c.vncsession(newc)
        res=c.list()
        res.write(2)
        c.kill(newsession)
        res=c.list()
        res.write(2)
        
        
    except Exception:
        print "ERROR OCCURRED HERE"
        raise
  
