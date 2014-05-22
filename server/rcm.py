#!/bin/env python
import pickle
import datetime


class rcm_session:

    def __init__(self,fromstring='',fromfile='',file='',sessionname='',state='',node='',tunnel='',sessiontype='',nodelogin='',display='',jobid='',sessionid='',username='',walltime='',otp='', vncpassword=''):
        self.hash={'file':'','session name':'', 'state':'', 'node':'','tunnel':'','sessiontype':'', 'nodelogin':'', 'display':'', 'jobid':'', 'sessionid':'', 'username':'', 'walltime':'00:00:00','timeleft':'00:00:00', 'otp':'', 'vncpassword':''}
        if (fromfile != ''):
            self.hash=pickle.load(open(fromfile,"rb"))
        elif (fromstring != ''):
            self.hash=pickle.loads(fromstring)
        else:
            self.hash={'file':file, 'session name':sessionname ,'state':state, 'node':node, 'tunnel':tunnel, 'sessiontype':sessiontype, 'nodelogin':nodelogin,  'display':display, 'jobid':jobid, 'sessionid':sessionid, 'username':username, 'walltime':walltime,'timeleft':walltime, 'otp':otp, 'vncpassword':vncpassword}
            self.hash['created']=datetime.datetime.now().strftime("%Y%m%d-%H:%M:%S")
            
    def serialize(self,file):
        pickle.dump(self.hash, open( file, "wb" ) )

    def write(self,format):
        print "server output->"
        if ( format == 0):
            print pickle.dumps(self.hash)
        elif ( format == 1):
            for k in self.hash.keys():
                print "%s;%s" % ( k , self.hash[k] )
        elif ( format == 2):
            x=[]
            #for k in sorted(self.hash.keys()):
            for k in self.hash.keys():
                x.append(self.hash[k])
            print ";".join(x) 



class rcm_sessions:

    def __init__(self,fromstring='',fromfile='',sessions=[]):
        if (fromfile != ''):
            self.array=pickle.load(fromfile)
        elif (fromstring != ''):
            self.array=pickle.loads(fromstring)
        else:
            self.array=sessions

    def serialize(self,file):
        pickle.dump(self.array, open( file, "wb" ) )

    def write(self,format):
        print "server output->"
        if ( format == 0):
            print pickle.dumps(self.array)
        elif ( format == 1):
            for k in self.array:
                print "---------------------"
                k.write(1)
        elif ( format == 2):
            c=rcm_session()
            print ";".join(sorted(c.hash.keys())) 
            for k in self.array:
                k.write(2)

 
