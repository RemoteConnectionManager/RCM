import os
import sys
import socket
import ConfigParser
import enumerate_interfaces
import string

class baseconfig:
    def __init__(self):
        self.confdict=dict()
	self.sections=dict()
	self.options=dict()

    def parse(self,configfile=''):
        config = ConfigParser.RawConfigParser()
	if(not configfile):
	    myPath =   os.path.join(
                        os.path.dirname(
                         os.path.dirname(
                          os.path.abspath(__file__)
                         )
                        ),'config')
            configfile=os.path.join(myPath, self.filename)

        if(not os.path.exists(configfile)):
            print "WARNING missing platform file -->"+configfile
            return(False)
#	print "parsing configfile-->",configfile
        config.read(configfile)
        for s in config.sections():
            for o in config.options(s):
		#print "confdict ",s,o,"-->",config.get(s, o)
                self.confdict[(s,o)]=config.get(s, o)
		self.sections[s]=self.sections.get(s,[])+[o]
		self.options[o]=self.options.get(o,[])+[s]

class versionconfig(baseconfig):
    def __init__(self):
	baseconfig.__init__(self)
        self.filename=os.path.join(os.path.dirname(os.path.abspath(__file__)),'versionRCM.cfg')
	self.parse()
    
    def get_checksum(self,buildPlatformString=''):
        checksum = self.confdict.get(('checksum',buildPlatformString),'')
        downloadurl = self.confdict.get(('url', buildPlatformString),'')
	return(checksum,downloadurl)

class platformconfig(baseconfig):
    def __init__(self):
	baseconfig.__init__(self)
        self.confdict[('platform','nodepostfix')]=''
        self.filename='platform.cfg'
	self.default_scheduler_name='ssh'
	self.parse()
	self.find_scheduler()
	self.import_scheduler()
        
    def max_user_session(self):
	#print "maxUserSessions-->",self.confdict.get(('platform','maxusersessions'),2)
	return int(self.confdict.get(('platform','maxusersessions'),2))
    
    def find_scheduler(self):
        self.hostname = socket.gethostname()
        #print "hostname-->"+hostname+"<--"
        self.scheduler_name=self.confdict.get(('platform',self.hostname),self.default_scheduler_name)
        
    def get_vnc_menu(self):
	menu=dict()
	for vnc_id in self.sections['vnc_menu']:
	  menu_item_string=self.confdict[('vnc_menu',vnc_id)]
	  m=menu_item_string.split('|',1)
	  if ( len(m) > 1 ) :
	    item=m[0]
	    info=m[1]
	  else:
            item=vnc_id
	    info=menu_item_string
	  menu[vnc_id]=(item,info)
	return(menu)

    def vnc_attribute(self,vnc_id,section):
	names=vnc_id.split('_')
	prev=names[0]
	nodelogin = socket.gethostname()
        
	for name in [vnc_id]+names:
	  # Check if is present a specific setup for this node, otherwise get the default
          name_with_node = name + '@' + nodelogin
          found=self.confdict.get((section,name_with_node),None)
          if not found: 
            found=self.confdict.get((section,name),None)
	  if(found): 
            ret=string.Template(found).safe_substitute(__VNC_ID__=vnc_id,__VNC_PREV_MATCH__=prev,__VNC_TOP_MATCH__=names[0])
#	    print "found-->",found,"<-- ret-->",ret,"<--"
            return ret
	  prev=name
	return ''
  
    def vnc_subst(self,vnc_id):
	subst=dict()
	for s in self.sections:
	  if s.startswith('vnc_'): 
            subst[s]=self.vnc_attribute(vnc_id,s)
        return subst
		  
    def vnc_attrib_subst(self,vnc_id,section,subst=dict()):
	if self.sections.has_key(section):
	  v_subst=self.vnc_subst(vnc_id)
	  found=v_subst.get(section,None)
	  if(found):
	    f1=string.Template(found).safe_substitute(subst)
	    us=dict()
	    for s in v_subst:
	      us[s]=string.Template(v_subst[s]).safe_substitute(subst)
	    ret=string.Template(f1).safe_substitute(us)
	    return ret
	return ''

    def get_queues(self):
	return self.sections['jobscript']
    
    def get_queue_par(self,parname=''):
	pars=dict()
	for q in self.get_queues():
	  par=self.confdict.get((parname,q),None)
	  if(par): pars[q]=par
	return pars
	
    def get_testjobs(self):
	return self.get_queue_par('testjobscript')
	
    def get_jobscript(self,queue):
	return self.confdict.get(('jobscript',queue),self.confdict.get(('jobscript',self.default_scheduler_name),''))
	
    def get_queue(self,queue):
	q=dict()
	for tag in self.options.get(queue,[]):
	  q[tag]=self.confdict.get((tag,queue),None)
	return q
	
    def import_scheduler(self):
	#sys.stderr.write("####### importing scheduler####-->"+self.scheduler_name)
	if(self.default_scheduler_name == self.scheduler_name):
		self.session_tag = self.hostname
	else:
		self.session_tag = self.scheduler_name
	exec("import rcm_server_"+self.scheduler_name+" as rcm_scheduler")
	self.scheduler=rcm_scheduler
#	return (rcm_scheduler,session_tag)
	
    def get_rcm_server(self):
	return self.scheduler.rcm_server(self)
    
    def hack_login(self,subnet,nodelogin):
	return self.confdict.get((subnet,nodelogin),nodelogin)
    
    def get_login(self,subnet=''):
	nodelogin=''
	if(subnet):
	    nodelogin = enumerate_interfaces.external_name(subnet)
#	    print "enumerate_interface nodelogin---->",nodelogin
            if(not nodelogin):
                nodelogin = socket.getfqdn()
#	        print "socket.getfqdn nodelogin---->",nodelogin
	    nodelogin=self.hack_login(subnet,nodelogin)
        return nodelogin


if __name__ == '__main__':
    v=versionconfig()
    #print v.sections
    #print v.options
    print "versions-->",v.get_checksum('linux_64bit')
    
    
    p=platformconfig()
    #print p.confdict
    #print p.sections
    #print p.options
    print "scheduler_name-->"+p.scheduler_name
    print "session_tag-->"+p.session_tag
    print "scheduler-->",p.scheduler
    s=dict()
    s['geometry']='100x100'
    s['authfile']='$HOME/myauth'
    print "\n\n#########################\n\n"
    for id,m in p.get_vnc_menu().iteritems():
      print "item id ",id,m[0]," >>",m[1],"<< command>>",p.vnc_attrib_subst(id,'vnc_command',subst=s),"<< setup>>",p.vnc_attribute(id,'module_setup')
    print "\n\n#########################\n\n"
    
    print p.get_queues()
    for q in p.get_queues() +['inesistente']:
        print "queue->"+q+"< has job\n--->"+p.get_jobscript(q)+"<------"
    print "queue visual has:\n",p.get_queue('visual'),"\n---------------------------------"
    print p.get_testjobs()
    login='rvn03.plx.cineca.it'
    for subnet in ['10.139.7','130.186.1']:
    	print "hack login nameson subnet: ",subnet,login,"-->", p.hack_login(subnet,login)
	print "get_login-->"+str(p.get_login(subnet))
    print "instance a server"
    s=p.get_rcm_server()
    print "available queues-->"+str(s.get_queue(p.get_testjobs()))
    
    print "versions-->",v.get_checksum('linux_64bit')
    
    
    
    
    
    
