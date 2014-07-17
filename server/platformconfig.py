import os
import socket

class platformconfig:
    def __init__(self):
        self.confdict=dict()
        self.confdict[('platform','nodepostfix')]=''
	self.sessions=dict()
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
		self.sessions[s]=self.sessions.get(s,[])+[o]
		self.options[o]=self.options.get(o,[])+[s]
        
    def scheduler(self):
        hostname = socket.gethostname()
        print "hostname-->"+hostname+"<--"
        scheduler=self.confdict.get(('platform',hostname),'ssh')
        return scheduler
    
    def get_queues(self):
	return self.sessions['jobscript']
	
    def get_queue(self,queue):
	q=dict()
	for tag in self.options.get(queue,[]):
	  q[tag]=self.confdict.get((tag,queue),None)
	return q


if __name__ == '__main__':
    p=platformconfig()
    p.parse()
    #print p.confdict
    print p.sessions
    print p.options
    print p.scheduler()
    print p.get_queues()
    print p.get_queue('visual')