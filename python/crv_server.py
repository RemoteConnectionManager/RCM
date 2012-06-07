#!/bin/env python
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
sys.path.append( sys.path[0] )
import crv

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
    raise Exception("Previous command failed (stderr reported above)!")
  return (r,o,e)


def short_jobid(long_jobid):
  sjid=long_jobid
  mo=re.match(r'(\d+)\.',long_jobid)
  if (mo):
    sjid=mo.group(1)
  return sjid

class crv_server:
  
  def __init__(self,pars):
    self.max_user_session=10
    self.qsub_template="""#!/bin/bash
#PBS -l walltime=$CRV_WALLTIME
#PBS -N $CRV_SESSIONID
#PBS -o $CRV_JOBLOG
#PBS -l "select=1:Qlist=visual:viscons=1"
#PBS -j oe
#PBS -q visual
#PBS -A cinstaff
#PBS -W group_list=cinstaff

. /cineca/prod/environment/module/3.1.6/none/init/bash
module purge
module load profile/advanced && module load TurboVNC 
vncserver -otp -fg > $CRV_JOBLOG.vnc 2>&1
"""
    self.executable=sys.argv[0]
    self.parameters=sys.argv[1:]
    self.username=pwd.getpwuid(os.geteuid())[0]
    self.available_formats=frozenset(['0','1','2'])
    self.available_commands=frozenset(['list','new','kill','otp'])
    self.parse_args()

  def usage(self,stderr=0):
    script=os.path.basename(self.executable)
    help="""
USAGE: %s [-u USERNAME | -U ] [-f FORMAT] 	list
       %s 					kill 	SESSIONID [SESSIONID ...]
       %s 					otp 	SESSIONID 
       %s [-w WALLTIME] [-f FORMAT]  		new
       %s -h
""" % (script,script,script,script,script)
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
    self.par_w="6:00:00"

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
    if (self.par_command == 'list'):
      self.execute_list()
    elif (self.par_command == 'new'):
      self.execute_new()
    elif (self.par_command == 'kill'):
      self.execute_kill()
    elif (self.par_command == 'otp'):
      self.execute_otp()

  # return a dictionary { sessionid -> jobid }
  # jobid are the ones: 
  # - of user (if -R=false) 
  # - running
  # - on visual queue
  # - with name matching: crv-<alphanum>-<num>
  def get_jobs(self,U=False):
    (retval,stdout,stderr)=prex(['qstat'])
    if (retval != 0 ) :
      sys.write.stderr(stderr);
      raise Exception( 'qstat returned non zero value: ' + str(retval) )
    else:
      raw=stdout.split('\n')
      if (U):
        ure='\w+'
      else:
        ure=self.par_u
      #258118.node351    crv-cin0449a-10  cin0449a          00:00:06 R visual          
      r=re.compile(r'(?P<jid>\d+[\w\.]+) \s+ (?P<sid>crv-%s-\d+)  \s+ (%s) \s+ \S+ \s+ R \s+ visual  ' % (ure,ure) ,re.VERBOSE)
      jobs={}
      for j in raw:
        mo=r.match(j)
        if (mo): 
          sid=mo.group('sid')
          jid=mo.group('jid')
          jobs[sid]=jid
      return(jobs)

  def get_crvdirs(self,U=False):
    if (U):
      udirs=glob.glob("/plx/user*/*/.crv")
    else:
      udirs=[os.path.expanduser("~%s/.crv" % (self.par_u))]
    return(udirs)

  #fill
  # - self.sessions, a dict {sessionid -> { field -> value}}
  # - self.sids,  a dict  {statofsids -> [sid1,sid2,...] }
  def load_sessions(self,U=False,sessionids=[]):
    udirs=self.get_crvdirs(U)
    if (U):
      ure='\w+'
    else:
      ure=self.par_u

    #read sessions files
    r=re.compile(r'(?P<sid>crv-(?P<user>%s)-\d+)\.session$' % ure) 
    self.sessions={}
    for d in udirs:
      if os.path.isdir(d) and os.access(d, os.R_OK):
        for f in os.listdir(d):
          ro= r.match(f)
          if ro:
            file= d + '/' + f
            user=ro.group(2)
            sid=ro.group(1)
            try:
              self.sessions[sid]=crv.crv_session(fromfile=file)
            except:
              sys.stderr.write("WARNING: not valid session file (it could be rewritten): %s\n" % (file))

    #read sessions jobs
    jobs=self.get_jobs(U=U)

    #match jobs and files
    self.sids={'run':set([]),'err':set([]),'end':set([]),'ini':set([])}
    for sid, ses in self.sessions.items():
      if ( ses.hash['state'] ==  'init' ): #in initialization phase (probably locked)
        type='ini'
      else: 				   
        if sid in jobs.keys():
          job_jid=jobs[sid]
          file_jid=ses.hash['jobid']
          if ( job_jid == file_jid ):
            type='run'
          else:
            sys.stderr.write('STRONG WARNING: session file %s contains wrong jobid: %s (the running one is %s)\n' % (sid,file_jid,job_jid))
            type='err'
          del(jobs[sid])
        else:
          type='end'
      self.sids[type].add(sid)
    
    #warning on session jobs without session file
    for sid, jid in jobs.items():
      sys.stderr.write("WARNING: found crv job with session %s without session file: %s\n" % (sid,jid))
      self.sids['err'].add(sid)      

  def id2sid(self,id,user=''):
    if (not user):
      user=self.par_u
    return "crv-%s-%d" % (user,id)  

  #return
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

  def clean_files(self,sid):
    for d in self.get_crvdirs():
      if ( not os.path.isdir(d) ):
        os.mkdir(d)
        os.chmod(d,0755)
      for f in glob.glob("%s/%s.*" % (d,sid)):
        os.remove(f)
    

  def submit_job(self,sid):
    s=string.Template(self.qsub_template)
    otp='%s/%s.otp' % (self.get_crvdirs()[0],sid)
    if(os.path.isfile(otp)):
      os.remove(otp)
    file='%s/%s.job' % (self.get_crvdirs()[0],sid)
    fileout='%s/%s.joblog' % (self.get_crvdirs()[0],sid)
    batch=s.substitute(CRV_WALLTIME=self.par_w,CRV_SESSIONID=sid,CRV_JOBLOG=fileout)
    f=open(file,'w')
    f.write(batch)
    f.close()
    (res,out,err)=cprex(['qsub','-v',"CRV_OTP_FILE="+otp,file])
    r=re.match(r'(\d+\.\w+)(\.[\w\.]+)?$',out)
    if (r):
      return r.group(1)
    else:
      raise Exception("Unknown qsub output: %s" % (out))

  def wait_jobout(self,sid,timeout):
    r=re.compile(r"""^New 'X' desktop is (?P<node>\w+):(?P<display>\d+)""",re.MULTILINE)
    otp_regex=re.compile(r"""^Full control one-time password: (?P<otp>\d+)""",re.MULTILINE)
    jobout='%s/%s.joblog.vnc' % (self.get_crvdirs()[0],sid)
    secs=0
    step=1
    while(secs < timeout ):
      if (os.path.isfile(jobout)):
        f=open(jobout,'r')
        jo=f.read()
        x=r.search(jo)
        if (x):
          otp=otp_regex.search(jo)
          return (x.group('node'),x.group('display'),otp.group('otp')) 
      secs+=step
      ##FP sys.stderr.write('Waiting for job output, %d/%d\n' % (secs,timeout) )
      time.sleep(step)
    raise Exception("Timeouted (%d seconds) job not correcty running!!!" % (timeout) )

  def execute_list(self):
    self.load_sessions()
    s=crv.crv_sessions()
    for sid in self.sids['run']:
      s.array.append(self.sessions[sid])
    s.write(self.par_f)
    sys.exit(0)

  def execute_new(self):
    self.load_sessions()
    sid=self.new_sid()
    self.clean_files(sid)
    file='%s/%s.session' % (self.get_crvdirs()[0],sid)
    #put the 'inactive' lock
    c=crv.crv_session(state='init',sessionid=sid)
    c.serialize(file)
    jid='NOT_SUBMITTED'
    try:
      jid=self.submit_job(sid)
      (n,d,otp)=self.wait_jobout(sid,10)
      n+='ib0'
    except Exception:
      c=crv.crv_session(state='invalid',sessionid=sid)
      c.serialize(file)
      if (jid != 'NOT_SUBMITTED'):
        x=prex(['qdel',jid])
      raise
    c=crv.crv_session(state='valid',walltime=self.par_w,node=n,display=d,jobid=jid,sessionid=sid,username=self.par_u,otp=otp)
    c.serialize(file)
    c.write(self.par_f)
    sys.exit(0)

  def execute_kill(self):
    self.load_sessions(U=True)
    norun=[]
    for sid in self.par_command_args:
      if sid in self.sids['run']:
        jid=self.sessions[sid].hash['jobid']
        cprex(['qdel',jid])
      else:
        norun.append(sid)
    if (norun):
      print "Not running sids: %s" % ", ".join(norun)
      sys.exit(1)
    sys.exit(0) 

  def execute_otp(self):
    self.load_sessions(U=True)
    for sid in self.par_command_args:
      if sid in self.sids['run']:
        otp_file='%s/%s.otp' % (self.get_crvdirs()[0],sid)
        if os.path.exists(otp_file):
          curr_otp=open(otp_file,'r').read()
	  os.remove(otp_file)
          print curr_otp
          sys.exit(0)
    sys.exit(1)



  def execute_auto(self):
    pass
    #self.load_sessions()
    #if (len(self.sids['run']) > 0 ):
    #  c=sorted(self.sids['run'],key=lambda sid: self.sessions[sid].hash['created'])[0]
    #else:
    #first.write(self.par_f)
   
    
    

if __name__ == '__main__':
  c = crv_server(sys.argv)
  c.execute()
  
"""
jid=$(qsub -o ~/crv/rubbish/ -e ~/crv/rubbish/ ~/crv/lenta1.qsub) ; res=$?
j=${jid%%.*}
if [[ $res -ne 0 ]] ; then
  echo "ERR: comando qsub non funzia"
  exit 1
fi
#sleep 1
q=$(qstat -f $jid )
state=$(echo "$q" | grep job_state | awk 'BEGIN{FS=" = "}{print $2}')
echo $state | grep -q 'R' ; res=$?
COUNTER=0
while [[ $res -ne 0 ]]; do
  sleep 1
  q=$(qstat -f $jid )
  state=$(echo "$q" | grep job_state | awk 'BEGIN{FS=" = "}{print $2}');
  echo $state | grep -q 'R' ; res=$?
  echo " Waiting... "  
  let COUNTER=COUNTER+1
  if [[ ${COUNTER} -gt 30 ]]; then
     qdel $jid
     exit 1
  fi
done

echo $state | grep -q 'R' ; res=$?
if [[ $res -ne 0 ]] ; then
  echo "ERR: job $jid non diventa running"
  echo " I kill it! "
  qdel $jid
  exit 1
fi
node=$(echo "$q" | grep exec_host | awk 'BEGIN{FS=" = "}{print $2}')
node=${node%%/*}
sleep 2
vnc=$( cat ~/crv/vnclog.$jid | grep 'desktop is' | awk 'BEGIN{FS=":"}{print $2}' )
cat <<EOF
jid:$jid
node:$node
vnc:$vnc
EOF
exit 0
"""
