import os
import sys
import rcm

class rcm_protocol:
    def __init__(self,rcm_server=None):
	if(rcm_server):	self.rcm_server=rcm_server
	
    def config(self,build_platform=''):
        conf=rcm.rcm_config()
        if(build_platform):
            (check,url)=self.rcm_server.get_checksum(build_platform)
            conf.set_version(check,url)
        queueList = self.rcm_server.get_queue()
        for q in queueList:
            conf.add_queue(q)
        conf.serialize()


    def version(self,build_platform=''):
        print "get version"
        if (self.client_sendfunc):
            return self.client_sendfunc("version "+build_platform)

    def queue(self):
        queueList = self.rcm_server.get_queue()
        #return the list of avilable queue

#	print self.rcm_server.serverOutputString
#	print ' '.join(queueList)
        sys.stdout.write(self.rcm_server.serverOutputString)
        sys.stdout.write(' '.join(queueList))
	sys.stdout.flush()

    def loginlist(self,subnet=''):
#	import socket
        self.rcm_server.subnet = subnet
#        fullhostname = socket.getfqdn()
        self.rcm_server.fill_sessions_hash()
        s=rcm.rcm_sessions()
        for sid, ses in self.rcm_server.sessions.items():
            s.array.append(self.rcm_server.sessions[sid])
        sys.stdout.write(self.rcm_server.serverOutputString)
	sys.stdout.write(s.get_string())
	sys.stdout.flush()

    def list(self,subnet=''):
        self.rcm_server.subnet = subnet
        
        self.rcm_server.load_sessions()
        s=rcm.rcm_sessions()
        for sid in self.rcm_server.sids['run']:
            s.array.append(self.rcm_server.sessions[sid])
        sys.stdout.write(self.rcm_server.serverOutputString)
	sys.stdout.write(s.get_string())
	sys.stdout.flush()
    
    def new(self,geometry='',queue='',sessionname='',subnet='',vncpassword='',vncpassword_crypted='',vnc_command=''):
        print "create new vnc display session"
        if (self.client_sendfunc):
            return self.client_sendfunc(
                "new geometry="+geometry+
                " queue="+queue+
                " sessionname=" + '\'' + sessionname + '\'' +
                " subnet="+subnet+
                " vncpassword="+vncpassword+
                " vncpassword_crypted="+'\'' + vncpassword_crypted + '\''+
                " vnc_command="+vnc_command
            )

    def kill(self,session_id=''):
        print "kill vnc display session"
        if (self.client_sendfunc):
            return self.client_sendfunc("kill "+session_id)
