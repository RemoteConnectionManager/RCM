#import os.path
import os
import subprocess
import re
import glob
import string
import time
import datetime


# get group to be used submitting a job
def getQueueGroup(self,queue):
    if len(self.accountList) == 0:
      return ''
    else:
      #cineca deployment dependencies
      if( 'cin' in self.par_u):
        group="cinstaff"
      else:
        group="cin_visual"
      return group

def prex(cmd):
    cmdstring=cmd[0]
    for p in cmd[1:]:
      cmdstring+=" '%s'" % (p) 
    #sys.stderr.write("Executing: %s\n" % (cmdstring)  )
    myprocess = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout,stderr = myprocess.communicate()
    myprocess.wait()                        
    return (myprocess.returncode,stdout,stderr)     
  
def cprex(cmd):
    (r,o,e)=prex(cmd)
    if (r != 0):
      print e
      raise Exception("command {0} failed with error: {1}".format([cmd[0],cmd[-1]],e))
    return (r,o,e)

# submit a LL job
# stdout and stderr are separated in 2 files
def submit_job(self,sid,rcm_dirs,jobScript):
    #cineca deployment dependencies
    self.ll_template="""
#!/bin/bash
# @ job_type = serial
# @ job_name = $RCM_SESSIONID
# @ output = $RCM_JOBLOG
# @ error = $RCM_JOBLOG.err
# @ wall_clock_limit = $RCM_WALLTIME
# @ class = visual
# @ queue

module load profile/advanced
module load turbovnc
$RCM_CLEANPIDS

$RCM_VNCSERVER -otp -fg -novncauth > $RCM_JOBLOG.vnc 2>&1   
"""

    s=string.Template(self.ll_template)
    print s
    otp='%s/%s.otp' % (rcm_dirs[0],sid)
    if(os.path.isfile(otp)):
      os.remove(otp)
    file='%s/%s.job' % (rcm_dirs[0],sid)
    fileout='%s/%s.joblog' % (rcm_dirs[0],sid)
      
    batch=s.safe_substitute(RCM_WALLTIME=self.par_w,RCM_SESSIONID=sid,RCM_JOBLOG=fileout,RCM_QUEUE=self.queue,RCM_VNCSERVER=self.vncserver_string,RCM_CLEANPIDS=self.clean_pids_string)

    
    f=open(file,'w')
    f.write(batch)
    f.close()
    (res,out,err)=cprex(['llsubmit',file])

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
    cprex(['llcancel',jid])
    
    
# get available queues for the user (on Fermi class is visual?!)
def get_queue(self):
    queueList = []
    #tutti gli utenti possono sottomettere nella cosa serial??
    #cineca deployment dependencies
    queueList.append("visual")
    return queueList
      
# get running jobs
def get_jobs(self, sessions, U=False,):
    #(retval,stdout,stderr)=prex(['llq'])
    #get list of jobs: blank-delimited list of categories (job name, class, owner)
    (retval,stdout,stderr)=prex(['llq','-f','%id','%jn','%c','%o'])
    if (retval != 0 ) :
      sys.write.stderr(stderr);
      raise Exception( 'llq returned non zero value: ' + str(retval) )
    else:
      raw=stdout.split('\n')
      if (U):
        ure='\w+'
      else:
        ure=self.par_u
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
