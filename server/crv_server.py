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
  myprocess = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  stdout,stderr = myprocess.communicate()
  myprocess.wait()                        
  return (myprocess.returncode,stdout,stderr)     

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
# scrive log nella home utente
#PBS -l walltime=$CRV_WALLTIME
#PBS -N $CRV_SESSIONID
#PBS -o $CRV_JOBLOG
#PBS -j oe
#PBS -q visual
#PBS -A cinstaff
#PBS -W group_list=cinstaff

. /cineca/prod/environment/module/3.1.6/none/init/bash
module purge
module use /plx/userprod/pro3dwe1/BA/modulefiles/profiles && module load luigi/advanced && module load autoload VirtualGL && module load TurboVNC
mkdir -p ~/.crv
vncserver -fg 
date
"""
    self.executable=sys.argv[0]
    self.parameters=sys.argv[1:]
    self.username=pwd.getpwuid(os.geteuid())[0]
    self.available_formats=frozenset(['1'])
    self.available_commands=frozenset(['list','new','kill'])
    self.parse_args()


  def usage(self,stderr=0):
    script=os.path.basename(self.executable)
    help="""
USAGE: %s [-u USERNAME | -U ] [-f FORMAT] 	list
       %s 					kill 	JOBID [JOBID ...]
       %s [-w WALLTIME] [-f FORMAT]  		new
       %s -h
""" % (script,script,script,script)
    if (stderr):
      sys.stderr.write(help)
    else:
      sys.stdout.write(help)

  def parse_args(self):

    #default options
    self.par_U=False
    self.par_u=self.username
    self.par_f=1
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
        self.par_w=rew
      else:
        print "ABORT: wrong walltime: %s" % (doptions['-w'])
        sys.exit(1)

    self.u_home=os.path.expanduser("~%s" % (self.par_u))  

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

  # return a dictionary { sessionid -> jobid }
  # jobid are the ones: 
  # - of user (if -R=false) 
  # - running
  # - on visual queue
  # - with name matching: crv-<alphanum>-<num>
  def get_jobs(self,U=False):
    (retval,stdout,stderr)=prex(['qstat','-f'])
    if (retval != 0 ) :
      sys.write.stderr(stderr);
      raise Exception( 'qstat returned non zero value: ' + str(retval) )
    else:
      r=re.compile('^Job Id:',re.MULTILINE)
      raw=r.split(stdout)
      raw.pop(0)                  #discard first record, it should be void
      if (U):
        ure='\w+'
      else:
        ure=self.par_u
      #Job Id: 252575.node351.plx.cineca.it
      #    Job_Name = crv-cin0449a-23
      #    Job_Owner = aco1ss08@node342ib0.plx.cineca.it
      #    job_state = R
      #    Resource_List.Qlist = visual
      r=re.compile(r"""
                                 	      \s*  \d+[\w\.]+             .*
        \n  \s+  Job_Name    		\s+ = \s+  (?P<sid>crv-\w+-\d+)   .*
        \n  \s+  Job_Owner 		\s+ = \s+  %s        		  .*
        \n  \s+  Job_state 		\s+ = \s+       R   \s+           .*
        \n  \s+  Resource_List.Qlist 	\s+ = \s+  visual       
        """ % (ure) ,re.MULTILINE|re.VERBOSE|re.DOTALL)
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
      if os.path.isdir(d):
        for f in os.listdir(d):
          print "SESSIONS", d,f
          ro= r.match(f)
          if ro:
            file= d + '/' + f
            user=ro.group(2)
            sid=ro.group(1)
            try:
              self.sessions[sid]=crv.crv_session(fromfile=file)
            except:
              sys.stderr.write("WARNING: not valid session file (it could be rewritten): %s\n" % (file))

    print "ITEMS", self.sessions.items()
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
            del(jobs[sid])
          else:
            sys.stderr.write('STRONG WARNING: session file of sid %s contain wrong jobid: %s (the running one is %s)\n' % (sid,file_jid,job_jid))
            type='err'
        else:
          type='end'
      self.sids[type].add(sid)
    
    #warning on session jobs without session file
    for sid, jid in jobs:
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
      raise Exception("ERROR: max %d sessions: no more available (%d running, %d errored).\n" % (self.max_user_session,n_run,n_err))
    else:
      if ( n_all >= self.max_user_session ):
        #need to recycle a sid, the oldest 
        res=sorted(end,key=lambda sid: self.sessions[sid].hash('created'))[0]
      else:
        #pick an unused sid
        all=self.sids['err'] | self.sids['run'] | self.sids['end'] | self.sids['ini']
        print "ERR", self.sids
        #print "RUN", run
        #print "END", end
        #print "INI", ini
        for i in range(1,self.max_user_session + 1):
          sid=self.id2sid(i)
          print 'SID',sid,'ALL',all
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
    file='%s/%s.job' % (self.get_crvdirs()[0],sid)
    fileout='%s/%s.joblog' % (self.get_crvdirs()[0],sid)
    batch=s.substitute(CRV_WALLTIME=self.par_w,CRV_SESSIONID=sid,CRV_JOBLOG=fileout)
    f=open(file,'w')
    f.write(batch)
    f.close()
    (res,out,err)=prex(['qsub',file])
    if (res != 0):
      sys.stderr.write(err)
      raise Exception("Cannot submit job file: %s" % (file))        
    else:
      if (re.match(r'\d+\.[\w\.]+$',out)):
        return out
      else:
        raise Exception("Unknown qsub output: %s" % (out))

  def wait_jobout(self,sid,timeout):
    r=re.compile(r"""^New 'X' desktop is (?P<node>\w+):(?P<display>\d+)""",re.MULTILINE)
    jobout='%s/%s.jobout' % (self.get_crvdirs()[0],sid)
    secs=0
    while(secs < timeout ):
      if (os.path.isfile(jobout)):
        f=open(jobout,'r')
        jo=f.readlines()
        if (r.search(jo) ):
          return (r.group('node'),r.group('display')) 
      time.sleep(1)
    raise Exception("Timeouted (%d seconds) job!!!" % (timeout) )

  def execute_list(self):
    self.load_sessions()
    
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
      (n,d)=self.wait_jobout(jid,10)
    except Exception:
      c=crv.crv_session(state='invalid',sessionid=sid)
      print "FILE", file
      c.serialize(file)
      if (jid != 'NOT_SUBMITTED'):
        prex(['qdel',jid])
      raise
    c=crv.crv_session(state='valid',walltime=par_w,node=n,display=d,jobid=jid,sessionid=sid,username=par_u)
    c.serialize(file)
    c.write(self.par_f)

  def execute_kill(self):
    # self.load_session([XXX,YYY])
    # c=crv_session('file')
    # c.set('state','KILLED')
    # jid=c.get('jobid')
    # c.serialize(file)
    pass


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
