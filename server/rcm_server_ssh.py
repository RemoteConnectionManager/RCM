#import os.path
import os, stat
import subprocess
import re
import glob
import string
import time
import datetime

import rcm_base_server
class rcm_server(rcm_base_server.rcm_base_server):

  def vnc_command_in_background(self):
    return True

  def timeleft_string(self,sid):
	return self.notimeleft_string
# get group to be used submitting a job
  #def getQueueGroup(self,queue):
    #if len(self.accountList) == 0:
      #return ''
    #else:
      ##cineca deployment dependencies
      #if( 'cin' in self.username):
        #group="cinstaff"
      #else:
        #group="cin_visual"
      #return group

  def prex(self,cmd):
    cmdstring=cmd[0]
    for p in cmd[1:]:
      cmdstring+=" '%s'" % (p) 
    #sys.stderr.write("Executing: %s\n" % (cmdstring)  )
    print cmdstring
    myprocess = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    stdout,stderr = myprocess.communicate()
    myprocess.wait()
    print stdout
    return (myprocess.returncode,stdout,stderr)
  
  def cprex(self,cmd):
    (r,o,e)=self.prex(cmd)
    if (r != 0):
      print e
      raise Exception("command %s failed with error: %s" % ([cmd[0],cmd[-1]],e))
    return (r,o,e)

# submit a LL job
# stdout and stderr are separated in 2 files
  def submit_job(self,sid,rcm_dirs,jobScript):
    #cineca deployment dependencies
    self.ssh_template=jobScript
#"""
##!/bin/bash
#
#. /cineca/prod/environment/module/3.1.6/none/init/bash
#module purge
#module load profile/advanced
#module load turbovnc
#
#$RCM_CLEANPIDS
#
#echo -e $RCM_VNCPASSWD  | vncpasswd -f > $RCM_JOBLOG.pwd 
#
#$RCM_VNCSERVER -otp -rfbauth $RCM_JOBLOG.pwd > $RCM_JOBLOG.vnc 2>&1
#cat `ls -tr ~/.vnc/*.pid | tail -1`
#"""

    s=string.Template(self.ssh_template)
    print s
    otp='%s/%s.otp' % (rcm_dirs[0],sid)
    if(os.path.isfile(otp)):
      os.remove(otp)
    file='%s/%s.job' % (rcm_dirs[0],sid)
    fileout='%s/%s.joblog' % (rcm_dirs[0],sid)
    
    self.substitutions['RCM_JOBLOG'] = fileout
    self.substitutions['RCM_VNCSERVER']=string.Template(self.substitutions['RCM_VNCSERVER']).safe_substitute(self.substitutions)
    
    self.substitutions['RCM_CLEANPIDS']=self.clean_pids_string
    self.substitutions['RCM_VNCPASSWD']=self.vncpassword
      
    batch=s.safe_substitute(self.substitutions)
    print "batch------------------------\n",batch
#    batch=s.safe_substitute(RCM_MODULE_SETUP=self.vnc_setup,RCM_JOBLOG=fileout,RCM_VNCSERVER=self.vncserver_string,RCM_CLEANPIDS=self.clean_pids_string,RCM_VNCPASSWD=self.vncpassword)

    
    f=open(file,'w')
    f.write(batch)
    f.close()
    os.chmod(file, stat.S_IRWXU)
    (res,out,err)=self.cprex([file])
    
    if (res != 0 ) :
      sys.write.stderr(err);
      raise Exception( 'Creation of remote display failed: ' + str(err) )
    else:
      return out.rstrip() #out is the pid of Xvnc


# kill a PBS job
  def kill_job(self,jid):
    #cprex(['qdel',jid])
    #cprex(['kill '+ jid])
    try:
      os.kill(int(jid), 9)
    except:
      raise Exception("Can not kill Xvnc process with pid: %s." % (jid))
    
    
# get available queues for the user (ssh in no job scheduler)
  def get_queue(self,testJobScriptDict=None):
    queueList = []
    queueList.append("ssh")
    return queueList
      
# get running jobs
  def get_jobs(self, U=False):
    #(retval,stdout,stderr)=prex(['llq'])
    #get list of jobs: blank-delimited list of categories (job name, class, owner)
    pidList = []
    
    p1 = subprocess.Popen(["ps","-u",self.username], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout,stderr = p1.communicate()
    row=stdout.split('\n')
    row = filter(None, row)
    for j in row:
      if "Xvnc" in j:
        pidList.append(j.lstrip().split(' ')[0]) #get list of pid

    jobs={} 
    for sid, ses in self.sessions.items():
      file_jid=ses.hash['jobid']
      if file_jid in pidList:
        jobs[sid]=file_jid #check if jobid in session file is a running pid
    print jobs
    return (jobs)

if __name__ == '__main__':
	s=rcm_server()
	print "accounts:",s.getUserAccounts()
	print "rcmdirs:",s.get_rcmdirs()
	print "fill_sessions_hash:",s.fill_sessions_hash()
	print "load sessions:",s.load_sessions()