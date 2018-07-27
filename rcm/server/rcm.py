#!/bin/env python
import pickle
import json
import datetime
import sys
import os
import logging

#from  logger_server import logger

logger = logging.getLogger('RCM.protocol')

logger.debug("Here in rcm")
sys.path.append( os.path.dirname(os.path.abspath(__file__))  )
"""
Decide which format should use
"""
format_default = 'json'
serverOutputString = "server output->"

class rcm_session:

    def __init__(self,fromstring='',fromfile='',file='',sessionname='',state='',node='',tunnel='',sessiontype='',nodelogin='',display='',jobid='',sessionid='',username='',walltime='',otp='', vncpassword=''):
        self.hash={'file':'','session name':'', 'state':'', 'node':'','tunnel':'','sessiontype':'', 'nodelogin':'', 'display':'', 'jobid':'', 'sessionid':'', 'username':'', 'walltime':'00:00:00','timeleft':'00:00:00', 'otp':'', 'vncpassword':''}
        if (fromfile != ''):
            with open(fromfile, 'r') as content_file:
                fromstring = content_file.read()
            if fromstring[0] == '(':
                logger.debug("USING PIKLE for rcm_session fromfile " + fromfile)
                self.hash = pickle.load(open(fromfile,"rb"))
            elif format_default == 'json':
                logger.debug("USING JSON for rcm_session fromfile " + fromfile)
                self.hash = json.load(open(fromfile, "r"))
            self.hash['file']=fromfile
        elif (fromstring != ''):
            if fromstring[0] == '(':
                logger.debug("USING PIKLE for rcm_session fromstring--" + fromstring[0])
                self.hash = pickle.loads(fromstring.encode('utf-8'))
            elif format_default == 'json':
                logger.debug("USING JSON  for rcm_session fromstring--" + fromstring[0])
                self.hash = json.loads(fromstring)
        else:
            self.hash={'file':file, 'session name':sessionname ,'state':state, 'node':node, 'tunnel':tunnel, 'sessiontype':sessiontype, 'nodelogin':nodelogin,  'display':display, 'jobid':jobid, 'sessionid':sessionid, 'username':username, 'walltime':walltime,'timeleft':walltime, 'otp':otp, 'vncpassword':vncpassword}
            self.hash['created']=datetime.datetime.now().strftime("%Y%m%d-%H:%M:%S")
            
    def serialize(self,file, format=format_default):
        logger.debug("USING "+ format + " for rcm_session.serialize on file " + file)
        if format == 'pickle':
            pickle.dump(self.hash, open( file, "wb" ) )
        elif format == 'json':
            json.dump(self.hash, open(file,'w'), ensure_ascii=False, sort_keys=True, indent=4)

    def get_string(self, format=format_default):
        logger.debug("USING "+ format + " for rcm_session.get_string on file " )
        if format == 'pickle':
            return pickle.dumps(self.hash)
        elif format == 'json':
            return json.dumps(self.hash)

    def write(self,format):     
        logger.debug("write")
        #print "server output->"
        if ( format == 0):
            sys.stdout.write(serverOutputString+self.get_string())
        elif ( format == 1):
            for k in self.hash.keys():
                print("%s;%s" % ( k , self.hash[k] ))
        elif ( format == 2):
            x=[]
            #for k in sorted(self.hash.keys()):
            for k in self.hash.keys():
                x.append(self.hash[k])
            print(";".join(x))



class rcm_sessions:

    def __init__(self,fromstring='',fromfile='',sessions=[]): 
    
        self._array=[] 
        if (fromfile != ''):
            if format_default == 'pickle':
                self._array = pickle.load(open(fromfile,"rb"))
            elif format_default == 'json':
                self._array = json.load(open(fromfile, "r"))
        elif (fromstring != ''):
            if fromstring[0] == '(':
                logger.debug("USING PIKLE for rcm_sessions fromstring--"+fromstring[0])
                #self._array = pickle.loads(fromstring.encode('utf-8'))
                old_sessions = pickle.loads(fromstring.encode('utf-8'))
                for s in old_sessions:
                    self._array.append(s.hash)
            elif format_default == 'json':
                logger.debug("USING JSON for rcm_sessions fromstring--"+fromstring[0])
                hashes=json.loads(fromstring)
                for h in hashes:
                    self._array.append(h)
                #self._array = json.loads(fromstring)
        else:
            self._array=sessions

    def serialize(self, file, format):
        logger.debug("USING "+ format + " for rcm_sessions.serialize on file " + file)
        if format == 'pickle':
            pickle.dump(self._array, open( file, "wb" ) )
        elif format == 'json':
            json.dump(self._array, open(file,'w'), ensure_ascii=False, sort_keys=True, indent=4)

    def get_string(self, format=format_default):
        logger.debug("USING "+ format + " for rcm_sessions.get_string " )
        if format == 'pickle':
            return pickle.dumps(self._array)
        elif format == 'json':
            return json.dumps(self._array)

    def add_session(self,new_session):
        present=False
        for hash in self._array:
            if str(hash) == str(new_session.hash):
                logger.debug("Adding duplicate session "+ str(new_session.hash)  )
                present=True
                break
        if not present:
            self._array.append(new_session.hash)

    def get_sessions(self):
        out_sess=[]
        for h in self._array:
            s=rcm_session()
            s.hash=h
            out_sess.append(s)
        return out_sess

    def write(self,format=0):
        logger.debug("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ rcm_sessions.write @@@@@@@@@@@@@@@@@")
        #print "server output->"
        if ( format == 0):
            sys.stdout.write(serverOutputString+self.get_string())
        elif ( format == 1):
            for k in self._array:
                print("---------------------")
                k.write(1)
        elif ( format == 2):
            c=rcm_session()
            print(";".join(sorted(c.hash.keys())))
            for k in self._array:
                k.write(2)

 
class rcm_config:

    def __init__(self,fromstring='',fromfile=''): 

        if (fromfile != ''):
            if format_default == 'pickle':
                self.config = pickle.load(open(fromfile,"rb"))
            elif format_default == 'json':
                self.config = json.load(open(fromfile, "r"))
        elif (fromstring != ''):
            if fromstring[0] == '(':
                logger.debug("USING PIKLE for rcm_config fromstring--"+fromstring[0])
                self.config = pickle.loads(fromstring.encode('utf-8'))
            elif format_default == 'json':
                self.config = json.loads(fromstring)
        else:
            self.config={'version':{'checksum':'','url':''},'queues':dict(),'vnc_commands':dict()}
        
    def set_version(self,check,url):
        logger.debug("set_version")
        self.config['version']['checksum']=check
        self.config['version']['url']=url
        
    def get_version(self):
        logger.debug("get_version")
        return (self.config.get('version',dict()).get('checksum',''),self.config.get('version',dict()).get('url',''))

    def add_queue(self,queue,info=''):
        logger.debug("add_queue")
        self.config['queues'][queue]=info
        
    def add_vnc(self,vnc,entry=None):
        logger.debug("add_vnc")
        if(not entry):
            entry=(vnc,'')
        self.config['vnc_commands'][vnc]=entry

    def get_string(self, format=format_default):

        logger.debug("USING "+ format + " for rcm_config.get_string " )
        if format == 'pickle':
            return pickle.dumps(self.config)
        elif format == 'json':
            return json.dumps(self.config)

    def serialize(self,file='',format=format_default):

        logger.debug("USING "+ format + " for rcm_config.serialize on file " + file)

        if (file != ''):
            if format == 'pickle':
                pickle.dump(self.config, open( file, "wb" ) )
            elif format == 'json':
                json.dump(self.config, open(file, 'w'), ensure_ascii=False, sort_keys=True, indent=4)
        else:
            #print pickle.dumps(self.config)
            sys.stdout.write(serverOutputString+self.get_string())

    def pretty_print(self):

        logger.debug("pretty_print:version: checksum->"+self.config['version']['checksum']+'<--url ->'+self.config['version']['url'])
        print()
        for queue in self.config['queues']:
            logger.debug("queue "+queue+" info--"+self.config['queues'][queue]+"--")
        logger.debug("")
        for vnc in sorted(self.config['vnc_commands'].keys()):
            logger.debug("vnc command "+vnc+" info--"+str(self.config['vnc_commands'][vnc])+"--")
            

if __name__ == '__main__':
    print("start testing..................................")
    void_config=rcm_config()
    print("void......-->"+void_config.get_string()+"<--")
    void_config.pretty_print()

    test_config=rcm_config()
    test_config.set_version('my cheksum','my url')
    test_config.add_queue('coda1','this is queue 1')
    test_config.add_queue('coda2','this is queue 2')
    test_config.add_vnc('vnc1','this is vnc 1')
    test_config.add_vnc('vnc2','this is vnc 2')
    test_config.add_vnc('vnc3')
    print("test......-->"+test_config.get_string()+"<--")
    test_config.pretty_print()
    
    print("test pack_unpack......-->"+test_config.get_string()+"<--")
    test_config.add_vnc('vnc4','added before unpack')
    derived=rcm_config(test_config.get_string())
    derived.add_vnc('vnc5','added after unpack')
    derived.pretty_print()

