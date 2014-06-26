import os
import socket

class platformconfig:
    def __init__(self):
        self.confdict=dict()
        self.confdict[('platform','nodepostfix')]=''

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
        
    def scheduler(self):
        hostname = socket.gethostname()
        print "hostname-->"+hostname+"<--"
        scheduler=self.confdict.get(('platform',hostname),'ssh')
        return scheduler

if __name__ == '__main__':
    p=platformconfig()
    p.parse()
    print p.confdict
    print p.scheduler()