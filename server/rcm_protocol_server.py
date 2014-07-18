import os
import rcm

class rcm_protocol:
    def __init__(self,rcm_server):
        self.rcm_server=rcm_server
    def config(self,build_platform=''):
        conf=rcm.rcm_config()
        if(build_platform):
            (check,url)=self.rcm_server.get_checksum(build_platform)
            conf.set_version(check,url)
        queueList = self.rcm_server.rcm_scheduler.get_queue(self.rcm_server.testJobScriptDict)
        for q in queueList:
            conf.add_queue(q)
        conf.serialize()


    def version(self,build_platform=''):
        print "get version"
        if (self.client_sendfunc):
            return self.client_sendfunc("version "+build_platform)

    def queue(self):
        print "get queues"
        if (self.client_sendfunc):
            return self.client_sendfunc("queue ")

    def loginlist(self,subnet=''):
        print "get login list "
        if (self.client_sendfunc):
            return self.client_sendfunc("loginlist "+subnet)

    def list(self,subnet=''):
        print "get display session list "
        if (self.client_sendfunc):
            return self.client_sendfunc("list "+subnet)
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
