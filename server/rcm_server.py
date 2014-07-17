#!/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import sys
import getopt
import os.path
import os
import pwd
import re
import glob
import string
import time
import shutil
import datetime
sys.path.append( sys.path[0] )
import ConfigParser
import rcm
import socket
import traceback

import enumerate_interfaces
import platformconfig

config = ConfigParser.RawConfigParser()
myPath =  os.path.dirname(os.path.abspath(__file__))
config.read(os.path.join(myPath, 'platform.cfg'))
nodepostfix = ''
importString=''
jobscript=''
walltimelimit="06:00:00"
hostname = socket.gethostname()
scheduler = ''
session_tag = '' #added to the session file name to identify who the session belongs to


try:
    if (config.has_option('platform',hostname)):
        scheduler = config.get('platform',hostname)
        importString="rcm_server_" + scheduler
        session_tag = scheduler
    else:
        importString="rcm_server_ssh"
        session_tag = hostname
    if (config.has_option('platform','nodepostfix')):
        nodepostfix=config.get('platform','nodepostfix')
    #if (config.has_option('platform','walltimelimit')):
    #  walltimelimit=config.get('platform','walltimelimit')

    maxUserSessions=2
    if (config.has_option('platform','maxUserSessions')):
        maxUserSessions=int(config.get('platform','maxUserSessions'))

    jobScriptDict = {}
    if (config.has_section('jobscript')):
        options = config.options('jobscript')
        for option in options:
            jobScriptDict[option]=config.get('jobscript',option)

    testJobScriptDict = {}
    if (config.has_section('testjobscript')):
        options = config.options('testjobscript')
        for option in options:
            testJobScriptDict[option]=config.get('testjobscript',option)
    
    wallTimeLimitDict = {}
    if (config.has_section('walltimelimit')):
        options = config.options('walltimelimit')
        for option in options:
            wallTimeLimitDict[option]=config.get('walltimelimit',option)

except Exception as e:
    raise Exception("Error in platform_config:{0}".format(e))

exec("import "+importString+" as rcm_scheduler")


def prex(cmd):
    cmdstring=cmd[0]
    for p in cmd[1:]:
        cmdstring+=" '%s'" % (p) 

    myprocess = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    uuuuuuustderr = myprocess.communicate()
    myprocess.wait()                        
    return (myprocess.returncode,stdout,stderr)     


def short_jobid(long_jobid):
    sjid=long_jobid
    mo=re.match(r'(\d+)\.',long_jobid)
    if (mo):
        sjid=mo.group(1)
    return sjid


class rcm_server:

    def getUserAccounts(self):
        #cineca deployment dependencies
        p1 = subprocess.Popen(["saldo","-nb"], stdout=subprocess.PIPE)
        stdout,stderr = p1.communicate()
        if 'not existing' in stdout:
            #old type user
            return []
        else:
            #now return a fixed group for experimentation
            #cineca deployment dependencies
            return ['cin_visual']

    def groupSubstitution(self, groupName, template):
        #print "groupName : ", groupName , "template: ", template
        if len(groupName) == 0:
            return ''
        else:
            return string.Template(template).substitute(RCM_GROUP=groupName)
        
    def getQueueGroup(self,queue):
        self.accountList = self.getUserAccounts()
        if len(self.accountList) == 0:
            return ''
        else:
            #cineca deployment dependencies
            if( 'cin' in self.par_u):
                group="cinstaff"
            else:
                group="cin_visual"
            return group
    
    
    def __init__(self,pars):
        self.max_user_session=maxUserSessions

        self.executable=sys.argv[0]
        self.parameters=sys.argv[1:]
        self.username=pwd.getpwuid(os.geteuid())[0]
        self.available_formats=frozenset(['0','1','2'])
        self.available_commands=frozenset(['loginlist','list','new','kill','otp','queue','version','config'])
        self.parse_args()
        #self.accountList = self.getUserAccounts()
        self.serverOutputString = 'server output->'

    def usage(self,stderr=0):
        script=os.path.basename(self.executable)
        help="""
    USAGE: %s [-u USERNAME | -U ] [-f FORMAT] 	loginlist
           %s 					list 
           %s 					kill 	SESSIONID [SESSIONID ...]
           %s 					otp 	SESSIONID 
           %s 					queue   ACCOUNT	
           %s [-w WALLTIME] [-f FORMAT]  		new
           %s 					version CLIENT_PLATFORM 
           %s -h
    """ % (script,script,script,script,script,script,script)
        if (stderr):
            sys.stderr.write(help)
        else:
            sys.stdout.write(help)

    def parse_args(self):

        #default options
        self.par_U=False
        self.par_u=self.username
        self.par_f='0'
        self.par_h=False
        self.subnet = ''
       
        #read arguments
        try:
            opts, args = getopt.getopt(self.parameters, 'u:Uf:q:w:h' )
        except getopt.GetoptError, err:
            sys.stderr.write(str(err))
            self.usage(stderr=1)
            sys.exit(1)
        doptions={}
        for o, a in opts:
            doptions[o]=a

        #overwrite default options 
        if ('-f' in doptions):
            if (doptions['-f'] in self.available_formats):
                self.par_f=doptions['-f']
            else:
                sys.stderr.write("ABORT: unknown format: %s\n" % (doptions['-f']))
                sys.exit(1)
        if ('-h' in doptions):
            self.par_h=True
        if ('-U' in doptions):
            self.par_U=True
        if ('-u' in doptions):
            try:
                self.par_u=pwd.getpwnam(doptions['-u'])[0]
            except KeyError:
                sys.stderr.write("ABORT: not existent username: %s\n" % (doptions['-u']))
                sys.exit(1)
        if ('-w' in doptions):
            rew=re.compile('((\d+:)?\d+:)?\d+(.\d+)?$') #[[hours:]minutes:]seconds[.milliseconds]
            if (rew.match(doptions['-w'])):
                self.par_w=doptions['-w']
            else:
                print "ABORT: wrong walltime: %s" % (doptions['-w'])
                sys.exit(1)

        self.u_home=os.path.expanduser("~%s" % (self.par_u))  
        self.par_f=int(self.par_f)

        # check arguments
        if (self.par_h):
            self.usage()
            sys.exit(0)
        elif (len(args)==0):
            sys.stderr.write("ABORT: no arguments specified.\n")
            self.usage(stderr=1)
            sys.exit(1)
        elif (args[0] in self.available_commands):
            self.par_command=args[0]
            self.par_command_args=args[1:]
        else:
            sys.stderr.write("ABORT: first argument unknown: %s\n" % (args[0]))
            self.usage(stderr=1)
            sys.exit(1)
 
    # check arguments/options match
    #TODO

    def execute(self):
        if (self.par_command == 'loginlist'):
            self.execute_loginlist()
        elif (self.par_command == 'list'):
            self.execute_list()
        elif (self.par_command == 'new'):
            self.execute_new()
        elif (self.par_command == 'kill'):
            self.execute_kill()
        elif (self.par_command == 'otp'):
            self.execute_otp()
        elif (self.par_command == 'queue'):
            self.execute_queue()
        elif (self.par_command == 'version'):
            self.execute_version()
        elif (self.par_command == 'config'):
            self.execute_config()

  # return a dictionary { sessionid -> jobid }
  # jobid are the ones: 
  # - of user (if -R=false) 
  # - running
  # - with name matching: rcm-<alphanum>-<num>
  #def get_jobs(self,sessions,U=False):
  #  return rcm_scheduler.get_jobs(self, sessions, U)
    

    def get_rcmdirs(self,U=False):
        if (U):
            #cineca deployment dependencies
            udirs=glob.glob("/plx/user*/*/.rcm") 
        else:
            #cineca deployment dependencies
            udirs=[os.path.expanduser("~%s/.rcm" % (self.par_u))]
        return(udirs)

  #fill
  # - self.sessions, a dict {sessionid -> { field -> value}}
  # - self.sids,  a dict  {statofsids -> [sid1,sid2,...] }
    def load_sessions(self,U=False,sessionids=[]):
        self.fill_sessions_hash()

        #read sessions jobs
        jobs=rcm_scheduler.get_jobs(self,self.sessions,U)

        #match jobs and files
        self.sids={'run':set([]),'err':set([]),'end':set([]),'ini':set([])}
        for sid, ses in self.sessions.items():
            if ses.hash.get('sessiontype','') == session_tag :
                if ( ses.hash['state'] ==  'init' ): #in initialization phase (probably locked)
                    type='ini'
                else: 				   
                    print jobs.keys()
                    if sid in jobs.keys():
                        job_jid=jobs[sid].strip()
                        file_jid=ses.hash['jobid'].strip()
                        if ( job_jid == file_jid ):
                            type='run'
                        else:
                            raise Exception("STRONG WARNING: session file# {0} contains wrong jobid: {1} (the running one is {2}".format(sid,file_jid,job_jid))
                        #type='err'
                        del(jobs[sid])
                    else:
                        type='end'
                self.sids[type].add(sid)
    
        #warning on session jobs without session file
        for sid, jid in jobs.items():
#            raise Exception("WARNING: found rcm job with session {0} without session file: {1}".format(sid,jid))
            print("WARNING: found rcm job with session {0} without session file: {1}".format(sid,jid))
            self.sids['err'].add(sid)   

    def fill_sessions_hash(self, U=False):

        udirs=self.get_rcmdirs(U)
        if (U):
            ure='\w+'
        else:
            ure=self.par_u

        #read sessions files
        r=re.compile(r'(?P<sid>(?P<user>%s)-(?P<tag>\S+)-\d+)\.session$' % ure) 
        self.sessions={}
        for d in udirs:
            if os.path.isdir(d) and os.access(d, os.R_OK):
                for f in os.listdir(d):
                    ro= r.match(f)
                    if ro:
                        file= d + '/' + f
                        user=ro.group(2)
                        sid=ro.group(1)
                        tag=ro.group(3)
                        #print "file-->",file
                        try:
                            self.sessions[sid]=rcm.rcm_session(fromfile=file)
                            #need the following lines to map nodes with different hostname from different subnet
                            originalNodeLogin = self.sessions[sid].hash.get('nodelogin','')
                            if (self.subnet != '' and originalNodeLogin != ''):
                                #originalNodeLogin = self.sessions[sid].hash['nodelogin']
                                if (config.has_option(self.subnet,originalNodeLogin)):
                                    originalNodeLogin = config.get(self.subnet,originalNodeLogin)
                                    self.sessions[sid].hash['nodelogin'] = originalNodeLogin

                            if (importString == "rcm_server_ssh"):
                                self.sessions[sid].hash['timeleft'] = "~"
                            else:
                                try:
                                    walltime = datetime.datetime.strptime(self.sessions[sid].hash['walltime'], "%H:%M:%S")
                                    endtime=datetime.datetime.strptime(self.sessions[sid].hash['created'], "%Y%m%d-%H:%M:%S") + datetime.timedelta(hours=walltime.hour,minutes=walltime.minute,seconds=walltime.second)      
                                    timedelta = endtime - datetime.datetime.now()
                                    #check if timedelta is positive
                                    if timedelta <= datetime.timedelta(0):
                                        timedelta = datetime.timedelta(0)
                                    self.sessions[sid].hash['timeleft'] = (((datetime.datetime.min + timedelta).time())).strftime("%H:%M:%S")

                                except:
                                    pass
                        except Exception as e:
                            raise Exception("WARNING: not valid session file %s: %s\n" % (file, e))

         

    def id2sid(self,id,user=''):
        if (not user):
            user=self.par_u
        return "{0}-{1}-{2}".format(user,session_tag,id)
        #return "rcm-%s-%t-%d" % (user,session_tag,id) #rcm-rmucci00-PBS-1


    def new_sid(self):
        n_err=len(self.sids['err'])
        n_run=len(self.sids['run'])
        n_end=len(self.sids['end'])
        n_ini=len(self.sids['ini'])
        n_loc= n_err + n_run + n_ini  #locked: can't reuse these sid
        n_all= n_loc + n_end
        if ( n_loc >= self.max_user_session ): 
            raise Exception("ERROR: max %d sessions: no more available (%d running, %d errored, %d initializing).\n" % (self.max_user_session,n_run,n_err,n_ini))
        else:
            if ( n_all >= self.max_user_session ):
                #need to recycle a sid, the oldest 
                res=sorted(self.sids['end'],key=lambda sid: self.sessions[sid].hash['created'])[0]
            else:
                #pick an unused sid
                all=self.sids['err'] | self.sids['run'] | self.sids['end'] | self.sids['ini']
                for i in range(1,self.max_user_session + 1):
                    sid=self.id2sid(i)
                    if ( sid not in all):
                        res=sid
                        break
        return res        

    def desktop_setup(self):
        desktop_dest_dir=os.path.expanduser("~%s/Desktop/" % (self.par_u))
        if (not os.path.exists(desktop_dest_dir)):
            os.makedirs(desktop_dest_dir)
    
        desktop_source_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),'Desktop_setup')
        for f in glob.glob(desktop_source_dir + '/*.desktop' ):
            fDest = os.path.join(desktop_dest_dir, os.path.basename(f))
            if (os.path.exists(fDest)):
                if (open(f, 'r').read() == open(fDest, 'r').read()):
                    return 
            shutil.copy(f,desktop_dest_dir)
      
    def clean_files(self,sid):
        for d in self.get_rcmdirs():
            if ( not os.path.isdir(d) ):
                os.mkdir(d)
                os.chmod(d,0755)
            self.desktop_setup()
            for f in glob.glob("%s/%s.*" % (d,sid)):
                os.remove(f)
   
    def wait_jobout(self,sid,timeout):
        #Output depends on TurboVNC version!
        r=re.compile(r"""^New 'X' desktop is (?P<node>\w+):(?P<display>\d+)""",re.MULTILINE)
        r1=re.compile(r"""^Desktop '(.*)' started on display (?P<node>\w+):(?P<display>\d+)""",re.MULTILINE)
        r2=re.compile(r"""^New '(.*)' desktop is (?P<node>\w+):(?P<display>\d+)""",re.MULTILINE)

        #otp_regex=re.compile(r"""^Full control one-time password: (?P<otp>\d+)""",re.MULTILINE)
        jobout='%s/%s.joblog.vnc' % (self.get_rcmdirs()[0],sid)
        secs=0
        step=1
        while(secs < timeout ):
            if (os.path.isfile(jobout)):
                f=open(jobout,'r')
                jo=f.read()
                x=r.search(jo)
                if (x):
                    #otp=otp_regex.search(jo)
                    #if (otp):
                    #    return (x.group('node'),x.group('display'),otp.group('otp')) 
                    return (x.group('node'),x.group('display'),'')
                x=r1.search(jo)
                if (x):
                    #otp=otp_regex.search(jo)
                    #if (otp):
                    #    return (x.group('node'),x.group('display'),otp.group('otp')) 
                    return (x.group('node'),x.group('display'),'')
                x=r2.search(jo)
                if (x):
                    #otp=otp_regex.search(jo)
                    #if (otp):
                    #    return (x.group('node'),x.group('display'),otp.group('otp')) 
                    return (x.group('node'),x.group('display'),'')
            secs+=step
            ##FP sys.stderr.write('Waiting for job output, %d/%d\n' % (secs,timeout) )
            time.sleep(step)
        raise Exception("Timeouted (%d seconds) job not correcty running!!!" % (timeout) )
 

    def execute_loginlist(self):
        self.subnet = self.par_command_args[0]
        fullhostname = socket.getfqdn()
        self.fill_sessions_hash()
        s=rcm.rcm_sessions()
        for sid, ses in self.sessions.items():
            s.array.append(self.sessions[sid])
        s.write(self.par_f)
        sys.exit(0)


    
    def execute_list(self):
        self.subnet = self.par_command_args[0]
        self.load_sessions()
        s=rcm.rcm_sessions()
        for sid in self.sids['run']:
            s.array.append(self.sessions[sid])
        s.write(self.par_f)
        sys.exit(0)

    def execute_new(self):
        new_params=dict()
        for par in self.par_command_args :
            tmp=par.split('=',1)
            print "command: ", par
            new_params[tmp[0]]=tmp[1]
        self.vncserver_string= 'vncserver'
        #cineca deployment dependencies
        self.clean_pids_string="""
for d_p in $(vncserver  -list | grep ^: | cut -d: -f2 | cut -f 1,3 --output-delimiter=@); do
	i=$(echo $d_p | cut -d@ -f2)
	d=$(echo $d_p | cut -d@ -f1)
	a=$(ps -p $i -o comm=)
	if [ "x$a" == "x" ] ; then 
	  vncserver -kill  :$d 1>/dev/null
 	fi
done"""
        sessionname = ''
        if('geometry' in new_params):
            self.vncserver_string += ' -geometry ' + new_params['geometry']
        if('queue' in new_params):
            self.queue = new_params['queue']
        if('sessionname' in new_params):
            sessionname = new_params['sessionname']
        if('subnet' in new_params):
            self.subnet = new_params['subnet']
            self.nodelogin = enumerate_interfaces.external_name(self.subnet)
            if(not self.nodelogin):
                self.nodelogin = socket.getfqdn()
            if (config.has_option(self.subnet,self.nodelogin)):
                self.nodelogin = config.get(self.subnet,self.nodelogin)
            if(not self.nodelogin):
                raise Exception("Error in finding nodelogin")

        if('vncpassword' in new_params):
            self.vncpassword = new_params['vncpassword']
        if('vncpassword_crypted' in new_params):
            vncpassword_crypted = new_params['vncpassword_crypted']


        self.load_sessions() 
        sid=self.new_sid()
        self.clean_files(sid)
        udirs=self.get_rcmdirs()
        file='%s/%s.session' % (udirs[0],sid)
    
        #put the 'inactive' lock
        c=rcm.rcm_session(state='init',sessionid=sid)
        c.serialize(file)
        jid='NOT_SUBMITTED'
        if(importString == "rcm_server_ssh"):
            self.par_w = "~"
        else:
            self.par_w = wallTimeLimitDict[self.queue] 
        try:
            #set vncpasswd
            if (config.has_option("module_setup","turbovnc")):
                self.vnc_setup = config.get("module_setup","turbovnc")

            fileout='%s/%s.joblog' % (udirs[0],sid) + '.pwd'
            vncpasswd_command = self.vnc_setup +  "; echo -e " + self.vncpassword + " | vncpasswd -f > " + fileout
	    myprocess = subprocess.Popen([vncpasswd_command],stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
            stdout,stderr = myprocess.communicate()
            myprocess.wait()
            jobScript = ''
            if self.queue in jobScriptDict.keys():
                jobScript = jobScriptDict[self.queue]
	    elif 'ssh' in jobScriptDict.keys():
                jobScript = jobScriptDict['ssh']

            jid=rcm_scheduler.submit_job(self,sid,udirs,jobScript)
            c=rcm.rcm_session(state='pending', sessionname=sessionname, walltime=self.par_w, node='', tunnel='', sessiontype=session_tag, nodelogin=self.nodelogin, display='', jobid=jid, sessionid=sid, username=self.par_u, otp='', vncpassword=vncpassword_crypted)
            c.serialize(file)
            #c.write(self.par_f)
            (n,d,otp)=self.wait_jobout(sid,400)
            #here we test if hostname returned by jobout is the same host (ssh case)
            if(n == socket.gethostname()): 
                tunnel='n'
            else:
                tunnel='y'
            #n+='ib0'
        except Exception as e:
            c=rcm.rcm_session(state='invalid',sessionid=sid)
            c.serialize(file)
            if (jid != 'NOT_SUBMITTED'):
                rcm_scheduler.kill_job(self, jid)   
            raise Exception("Error in execute_new:{0}".format(e))
       
        c=rcm.rcm_session(state='valid', sessionname=sessionname, walltime=self.par_w, node=n, tunnel=tunnel, sessiontype=session_tag, nodelogin=self.nodelogin, display=d, jobid=jid, sessionid=sid, username=self.par_u, otp=otp, vncpassword=vncpassword_crypted)
        
        c.serialize(file)
        c.write(self.par_f)
        sys.exit(0)

    def execute_kill(self):
        self.load_sessions(self.par_U)
        norun=[]
        for sid in self.par_command_args:
            if sid in self.sids['run']:
                jid=self.sessions[sid].hash['jobid']
                rcm_scheduler.kill_job(self,jid)
                file='%s/%s.session' % (self.get_rcmdirs()[0],sid)
                c=rcm.rcm_session(fromfile=file)
                c.hash['state']='killing'
                c.serialize(file)
            else:
                norun.append(sid)
        if (norun):
            print "Not running sids: %s" % ", ".join(norun)
            sys.exit(1)
        sys.exit(0) 

    def execute_otp(self):
        self.load_sessions(self.par_U)
        for sid in self.par_command_args:
            if sid in self.sids['run']:
                otp_file='%s/%s.otp' % (self.get_rcmdirs()[0],sid)
                if os.path.exists(otp_file):
                    curr_otp=open(otp_file,'r').read()
                    os.remove(otp_file)
                    print curr_otp
                    sys.exit(0)
        sys.exit(1)

    def execute_queue(self):
        queueList = rcm_scheduler.get_queue(testJobScriptDict)
    
        #return the list of avilable queue
        sys.stdout.write(self.serverOutputString)
        sys.stdout.write(' '.join(queueList))
        sys.exit(0)
    
#    def platform_config(self):
#        self.config = ConfigParser.RawConfigParser()
#        myPath =  os.path.dirname(os.path.abspath(__file__))
#        self.config.read(os.path.join(myPath, 'platform.cfg'))
#        nodepostfix = ''
#        importString=''
#        try:
#            importString="rcm_server"+self.config.get('batchscheduler')
#            nodepostfix=self.config.get('nodepostfix')
#        except Exception as e:
#            raise Exception("Error in platform_config:{0}".format(e))
#            
#        exec("import "+importString+" as rcm_scheduler")
    
    
    
    def execute_version(self):
        buildPlatformString = self.par_command_args[0]
        config = ConfigParser.RawConfigParser()
        myPath =  os.path.dirname(os.path.abspath(__file__))
        config.read(os.path.join(myPath, 'versionRCM.cfg'))
        checksum = config.get('checksum', buildPlatformString)
        downloadurl = config.get('url', buildPlatformString)
        sys.stdout.write(self.serverOutputString)
        sys.stdout.write(checksum)
        sys.stdout.write(' ')
        sys.stdout.write(downloadurl)
        sys.exit(0) 
    
    def execute_config(self):
	conf=rcm.rcm_config()
        if(len(self.par_command_args) >0):
	  buildPlatformString = self.par_command_args[0]
          config = ConfigParser.RawConfigParser()
          myPath =  os.path.dirname(os.path.abspath(__file__))
          config.read(os.path.join(myPath, 'versionRCM.cfg'))
	
          checksum = config.get('checksum', buildPlatformString)
          downloadurl = config.get('url', buildPlatformString)
	
	  conf.set_version(checksum,downloadurl)
	  queueList = rcm_scheduler.get_queue(testJobScriptDict)
	  for q in queueList:
            conf.add_queue(q)
	conf.serialize()
        sys.exit(0) 
    
    
    def execute_auto(self):
        pass
        #self.load_sessions()
        #if (len(self.sids['run']) > 0 ):
        #  c=sorted(self.sids['run'],key=lambda sid: self.sessions[sid].hash['created'])[0]
        #else:
        #first.write(self.par_f)
       
    

if __name__ == '__main__':
    try:
        c = rcm_server(sys.argv)
        c.execute()
    except Exception as e:
        #send the error to the client
        sys.stderr.write("{0}: {1}RCM:EXCEPTION".format(e, traceback.format_exc()))

        sys.exit(1)



