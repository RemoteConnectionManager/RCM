import os.path
import os
import subprocess
import re
import glob
import string
import time
import datetime

import rcm_base_server
class rcm_server(rcm_base_server.rcm_base_server):

 def vnc_command_in_background(self):
    return False

# get group to be used submitting a job
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

 def prex(self, cmd):
    cmdstring=cmd[0]
    for p in cmd[1:]:
      cmdstring+=" '%s'" % (p) 
    #sys.stderr.write("Executing: %s\n" % (cmdstring)  )
    myprocess = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout,stderr = myprocess.communicate()
    myprocess.wait()                       
    return (myprocess.returncode,stdout,stderr)     
 
 def cprex(self, cmd):
    (r,o,e)=self.prex(cmd)
    if (r != 0):
      print e
      raise Exception("command %s failed with error: %s" % ([cmd[0],cmd[-1]],e))
    return (r,o,e)

# submit a LL job
# stdout and stderr are separated in 2 files
 def submit_job(self,sid,rcm_dirs,jobScript):
    #cineca deployment dependencies
    self.qsub_template=jobScript

    fileout='%s/%s.joblog' % (rcm_dirs[0],sid)



#    self.ll_template="""
##!/bin/bash
## @ job_type = serial
## @ job_name = $RCM_SESSIONID
## @ output = $RCM_JOBLOG
## @ error = $RCM_JOBLOG.err
## @ wall_clock_limit = $RCM_WALLTIME
## @ class = visual
## @ queue

#export TMPDIR=/tmp

#module load profile/advanced
#module load turbovnc
#$RCM_CLEANPIDS

#echo -e $RCM_VNCPASSWD  | vncpasswd -f > $RCM_JOBLOG.pwd
#$RCM_VNCSERVER -otp -fg -rfbauth $RCM_JOBLOG.pwd > $RCM_JOBLOG.vnc 2>&1
    #"""


    #s=string.Template(self.ll_template)
    #print s
    #otp='%s/%s.otp' % (rcm_dirs[0],sid)
    #if(os.path.isfile(otp)):
    #  os.remove(otp)
    #file='%s/%s.job' % (rcm_dirs[0],sid)
    #fileout='%s/%s.joblog' % (rcm_dirs[0],sid)

    s=string.Template(self.qsub_template)
    otp='%s/%s.otp' % (rcm_dirs[0],sid)
    if(os.path.isfile(otp)):
      os.remove(otp)
    file='%s/%s.job' % (rcm_dirs[0],sid)
    fileout='%s/%s.joblog' % (rcm_dirs[0],sid)

    self.substitutions['RCM_JOBLOG'] = fileout
    self.substitutions['RCM_VNCSERVER']=string.Template(self.substitutions['RCM_VNCSERVER']).safe_substitute(self.substitutions)

    self.substitutions['RCM_WALLTIME']=self.par_w
    self.substitutions['RCM_SESSIONID']=sid
    self.substitutions['RCM_QUEUE']=self.queue
    self.substitutions['RCM_CLEANPIDS']=self.clean_pids_string
    self.substitutions['RCM_VNCPASSWD']=self.vncpassword
	
	
    group = self.getQueueGroup(self.queue)
	

    batch=s.safe_substitute(self.substitutions)
    print "batch------------------------\n",batch
    #batch=s.safe_substitute(RCM_MODULE_SETUP=self.vnc_setup,RCM_WALLTIME=self.par_w,RCM_SESSIONID=sid,RCM_JOBLOG=fileout,RCM_QUEUE=self.queue,RCM_VNCSERVER=self.vncserver_string,RCM_CLEANPIDS=self.clean_pids_string, RCM_VNCPASSWD=self.vncpassword)
	
	
    f=open(file,'w')
    f.write(batch)
    f.close()
    (res,out,err)=self.cprex(['llsubmit',file])
	
    p = re.compile('^llsubmit:.*job\s+[^"]*"([^"]*)".*')
	
    for line in out.split("\n"):
        print line
        o = p.match(line)
        if (o):
            jid_complete = o.group(1)
            break
	           
    r = re.compile('^([^\.]*)\..*')
    r2 = re.compile('.*\.(\d+)$')
    ro = r.match(jid_complete)
    ro2 = r2.match(jid_complete)
    if (ro):
        if (ro2):
            #add ".0" becuse it's a non contatenated job
            return (ro.group(1) + "." + ro2.group(1) + ".0").strip()
   
    raise Exception("Unknown llsubmit output: %s" % (out))


# kill a PBS job
 def kill_job(self,jid):
    #cprex(['qdel',jid])
    self.cprex(['llcancel',jid])
   
   
# get available queues for the user (on Fermi class is visual?!)
 def get_queue(self,testJobScriptDict=None):
    queueList = []
    #tutti gli utenti possono sottomettere nella cosa serial??
    #cineca deployment dependencies
    queueList.append("visual")
    return queueList

     
# get running jobs
 def get_jobs(self, sessions, U=False,):
    #(retval,stdout,stderr)=prex(['llq'])
    #get list of jobs: blank-delimited list of categories (job name, class, owner)
    (retval,stdout,stderr)=self.prex(['llq','-f','%id','%jn','%c','%o'])
    if (retval != 0 ) :
      sys.write.stderr(stderr);
      raise Exception( 'llq returned non zero value: ' + str(retval) )
    else:
      raw=stdout.split('\n')
      if (U):
        ure='\w+'
      else:
        ure=self.username
      #258118.node351    rcm-cin0449a-10  cin0449a          00:00:06 R visual   
      #fen03.47217.0 rcm-cin0449a-10   serial     rmucci00
      r=re.compile(r'(?P<jid>.*) \s+ (?P<sid>%s-\S+\d+) \s+ (%s) \s+ (%s) ' % (ure,'visual',ure) ,re.VERBOSE)
      #r=re.compile(r'(?P<jid>\d+[\w\.]+) \s+ (?P<sid>rcm-%s-\d+)  \s+ (%s) \s+ \S+ \s+ R \s+ ' % (ure,ure) ,re.VERBOSE)
      jobs={}
      for j in raw:
        mo=r.match(j)
        if (mo): 
          sid=mo.group('sid')
          jid=mo.group('jid')
          jobs[sid]=jid
      print jobs
      return(jobs)

if __name__ == '__main__':
        s=rcm_server()
        print "accounts:",s.getUserAccounts()
        print "rcmdirs:",s.get_rcmdirs()
        print "fill_sessions_hash:",s.fill_sessions_hash()
        print "load sessions:",s.load_sessions()

