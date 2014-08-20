import os
import sys
import string
import glob
import re
import subprocess
import socket
import pwd
import traceback
import datetime
import time

import rcm
import platformconfig

class rcm_base_server:
    def __init__(self,pconfig=None):
	self.subnet = ''
	self.par_f='0'

	self.notimeleft_string="~"
	self.username=pwd.getpwuid(os.geteuid())[0]
	if(pconfig):
            self.pconfig=pconfig
	else:	 
	    self.pconfig=platformconfig.platformconfig()
	self.max_user_session=self.pconfig.max_user_session()
#	(sched,s_tag)=self.pconfig.get_import_scheduler()
	self.session_tag=self.pconfig.session_tag
	self.no_timeleft= self.pconfig.default_scheduler_name == self.pconfig.scheduler_name
	self.substitutions=dict()

    def get_timelimit(self):
	return self.pconfig.confdict.get(('walltimelimit',self.queue),self.notimeleft_string)
    
    def set_vnc_setup(self,id):
	if self.vnc_command_in_background(): self.substitutions['vnc_foreground']=''
        self.vnc_setup = self.pconfig.vnc_attrib_subst(id,'vnc_setup',subst=self.substitutions)
	self.substitutions['RCM_MODULE_SETUP']= self.vnc_setup
	self.substitutions['RCM_VNCSERVER'] = self.pconfig.vnc_attrib_subst(id,'vnc_command',subst=self.substitutions)

	#print "set vnc_setup to-->"+self.vnc_setup

    
    def get_checksum(self,buildPlatformString=''):
	platformconfig.versionconfig().get_checksum(buildPlatformString)
	return platformconfig.versionconfig().get_checksum(buildPlatformString)

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
            if( 'cin' in self.username):
                group="cinstaff"
            else:
                group="cin_visual"
            return group
    def get_jobs(self, U=False):    
	    sys.stderr.write( "\ncalled generic get_jobs: THIS SHOULD NEVER BE PRINTED!!!!!!")
	    return dict()
    def get_rcmdirs(self,U=False):
        if (U):
            #cineca deployment dependencies
            udirs=glob.glob("/plx/user*/*/.rcm") 
        else:
            #cineca deployment dependencies
            udirs=[os.path.expanduser("~%s/.rcm" % (self.username))]
        return(udirs)

    def timeleft_string(self,sid):
	if(self.no_timeleft) : return self.notimeleft_string
	try:
		walltime_py24 = time.strptime(self.sessions[sid].hash['walltime'], "%H:%M:%S")
		endtime_py24 = time.strptime(self.sessions[sid].hash['created'], "%Y%m%d-%H:%M:%S")
		walltime = datetime.datetime(*walltime_py24[0:6])
		endtime = datetime.datetime(*endtime_py24[0:6])
		endtime= endtime + datetime.timedelta(hours=walltime.hour,minutes=walltime.minute,seconds=walltime.second)      
		timedelta = endtime - datetime.datetime.now()
	#check if timedelta is positive
		if timedelta <= datetime.timedelta(0):
			timedelta = datetime.timedelta(0)
		timeleft = (((datetime.datetime.min + timedelta).time())).strftime("%H:%M:%S")
		return timeleft
	

	except Exception,inst:
		#sys.stderr.write("session->%s RCM:EXCEPTION %s: %s " % (sid,inst, traceback.format_exc()))
                #print("exception in getting time:",type(inst),inst.args,file=sys.stderr)

   		return self.notimeleft_string
  
  
  #fill
  # - self.sessions, a dict {sessionid -> { field -> value}}
  # - self.sids,  a dict  {statofsids -> [sid1,sid2,...] }
    def load_sessions(self,U=False,sessionids=[]):
        self.fill_sessions_hash()

        #read sessions jobs
        jobs=self.get_jobs(U)
        #print "jobs--->",jobs
        #match jobs and files
        self.sids={'run':set([]),'err':set([]),'end':set([]),'ini':set([])}
        for sid, ses in self.sessions.items():
            if ses.hash.get('sessiontype','') == self.session_tag :
                if ( ses.hash['state'] ==  'init' ): #in initialization phase (probably locked)
                    type='ini'
                else: 				   
#                    print jobs.keys()
                    if sid in jobs.keys():
                        job_jid=jobs[sid].strip()
                        file_jid=ses.hash['jobid'].strip()
                        if ( job_jid == file_jid ):
                            type='run'
                        else:
                            raise Exception("STRONG WARNING: session file# %s contains wrong jobid: %s (the running one is %s" % (sid,file_jid,job_jid))
                        #type='err'
                        del(jobs[sid])
                    else:
                        type='end'
                self.sids[type].add(sid)
    
        #warning on session jobs without session file
        for sid, jid in jobs.items():
#            raise Exception("WARNING: found rcm job with session {0} without session file: {1}".format(sid,jid))
            print("WARNING: found rcm job with session %s without session file: %s" % (sid,jid))
            self.sids['err'].add(sid)   

    def fill_sessions_hash(self, U=False):

        udirs=self.get_rcmdirs(U)
        if (U):
            ure='\w+'
        else:
            ure=self.username

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
                                self.sessions[sid].hash['nodelogin'] = self.pconfig.confdict.get((self.subnet,originalNodeLogin),originalNodeLogin)

			    self.sessions[sid].hash['timeleft']=self.timeleft_string(sid)
                        except Exception,inst:
                                #print("WARNING: not valid session file %s: %s\n" % (file, e),type(inst),inst.args,file=sys.stderr)
				sys.stderr.write("%s: %s RCM:EXCEPTION" % (inst, traceback.format_exc()))
#                            raise Exception("WARNING: not valid session file %s: %s\n" % (file, e))

         

    def id2sid(self,id,user=''):
        if (not user):
            user=self.username
        #return "{0}-{1}-{2}".format(user,session_tag,id)
        return "%s-%s-%d" % (user,self.session_tag,id)


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
        desktop_dest_dir=os.path.expanduser("~%s/Desktop/" % (self.username))
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


    def execute_new(self):
        self.clean_pids_string="""
for d_p in $(vncserver  -list | grep ^: | cut -d: -f2 | cut -f 1,3 --output-delimiter=@); do
	i=$(echo $d_p | cut -d@ -f2)
	d=$(echo $d_p | cut -d@ -f1)
	a=$(ps -p $i -o comm=)
	if [ "x$a" == "x" ] ; then 
	  vncserver -kill  :$d 1>/dev/null
 	fi
done"""
        if(self.subnet): self.nodelogin = self.pconfig.get_login(self.subnet)
        if(not self.nodelogin):
                raise Exception("Error in finding nodelogin")



        self.load_sessions() 
        sid=self.new_sid()
        self.clean_files(sid)
        udirs=self.get_rcmdirs()
        file='%s/%s.session' % (udirs[0],sid)
    
        #put the 'inactive' lock
        c=rcm.rcm_session(state='init',sessionid=sid)
        c.serialize(file)
        jid='NOT_SUBMITTED'
        self.par_w = self.get_timelimit()
        try:
            #set vncpasswd

            fileout='%s/%s.joblog' % (udirs[0],sid) + '.pwd'
            vncpasswd_command = self.vnc_setup +  "; echo -e " + self.vncpassword + " | vncpasswd -f > " + fileout
	    myprocess = subprocess.Popen([vncpasswd_command],stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
            stdout,stderr = myprocess.communicate()
            myprocess.wait()
            jobScript = self.pconfig.get_jobscript(self.queue)

            jid=self.submit_job(sid,udirs,jobScript)
            c=rcm.rcm_session(state='pending', sessionname=self.sessionname, walltime=self.par_w, node='', tunnel='', sessiontype=self.session_tag, nodelogin=self.nodelogin, display='', jobid=jid, sessionid=sid, username=self.username, otp='', vncpassword=self.vncpassword_crypted)
            c.serialize(file)
            #c.write(self.par_f)
            (n,d,otp)=self.wait_jobout(sid,400)
            #here we test if hostname returned by jobout is the same host (ssh case)
            if(n == socket.gethostname()): 
                tunnel='n'
            else:
                tunnel='y'
            #n+='ib0'
#        except Exception as e:
        except Exception,inst:
	    sys.stderr.write("%s: %s RCM:EXCEPTION" % (inst, traceback.format_exc()))
		    
            c=rcm.rcm_session(state='invalid',sessionid=sid)
            c.serialize(file)
            if (jid != 'NOT_SUBMITTED'):
                self.kill_job(jid)   
            raise Exception("Error in execute_new:%s" % inst)
       
        c=rcm.rcm_session(state='valid', sessionname=self.sessionname, walltime=self.par_w, node=n, tunnel=tunnel, sessiontype=self.session_tag, nodelogin=self.nodelogin, display=d, jobid=jid, sessionid=sid, username=self.username, otp=otp, vncpassword=self.vncpassword_crypted)
        
        c.serialize(file)
        c.write(0)
	sys.stdout.flush()
        #sys.exit(0)

if __name__ == '__main__':
	s=rcm_base_server()
	print "accounts:",s.getUserAccounts()
	print "rcmdirs:",s.get_rcmdirs()
	print "fill_sessions_hash:",s.fill_sessions_hash()
	print "load sessions:",s.load_sessions()
