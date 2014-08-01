import os
import socket

class platformconfig:
    def __init__(self):
        self.confdict=dict()
        self.confdict[('platform','nodepostfix')]=''
	self.sections=dict()
	self.options=dict()

    def parse(self):
        import ConfigParser
        config = ConfigParser.RawConfigParser()
        myPath =  os.path.dirname(os.path.abspath(__file__))
        configfile=os.path.join(myPath, 'platform.cfg')
        if(not os.path.exists(configfile)):
            print "WARNING missing platform file -->"+configfile
            return(False)
        config.read(configfile)
        for s in config.sections():
            for o in config.options(s):
                self.confdict[(s,o)]=config.get(s, o)
		self.sections[s]=self.sections.get(s,[])+[o]
		self.options[o]=self.options.get(o,[])+[s]
        
    def scheduler(self):
        hostname = socket.gethostname()
        #print "hostname-->"+hostname+"<--"
        scheduler=self.confdict.get(('platform',hostname),'ssh')
        return scheduler
    
    def get_queues(self):
	return self.sections['jobscript']
    
    def get_testjobs(self):
	tetst_job_scripts=dict()
	for q in self.get_queues():
	  script=self.confdict.get(('testjobscript',q),None)
	  if(script): tetst_job_scripts[q]=script
	return tetst_job_scripts
	
    def get_queue(self,queue):
	q=dict()
	for tag in self.options.get(queue,[]):
	  q[tag]=self.confdict.get((tag,queue),None)
	return q
	
    def get_import_scheduler(self):
	def_sched="ssh"
	hostname = socket.gethostname()
	scheduler = self.confdict.get(('platform',hostname),def_sched)
	if(def_sched == scheduler):
		session_tag = hostname
	else:
		session_tag = scheduler
	exec("import rcm_server_"+scheduler+" as rcm_scheduler")
	return (rcm_scheduler,session_tag)
	



if __name__ == '__main__':
    p=platformconfig()
    p.parse()
    #print p.confdict
    print p.sections
    print p.options
    print p.scheduler()
    print p.get_queues()
    print p.get_queue('visual')
    print p.get_testjobs()
    subnet='10.139.7'
    login='rvn03.plx.cineca.it'
    print "hack login nameson subnet: ",subnet,login,"-->", p.confdict.get((subnet,login),login)
    subnet='130.186.1'
    print "hack login nameson subnet: ",subnet,login,"-->", p.confdict.get((subnet,login),login)
    (sched,s_tag)=p.get_import_scheduler()
    print "session_tag-->",s_tag
    print "instance a server"
    s=sched.rcm_server()
    print "available queues-->"+str(s.get_queue(p.get_testjobs()))