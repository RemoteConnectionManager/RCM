#!/bin/env python
# Esegue il qsub di un job che lancia un vnc server.
# Se ok ritorna valore 0 e in stdout stampa i valori di connessione
# jid:<job identifier>
# node:<nodo destinazione del job>
# vnc:<display ottenuto del server>
# Se non ok torna valore <> 0 e stampa in stdout un msg di errore
import subprocess
import sys
import getopt
import os.path
import os
import pwd
import re
import glob
sys.path.append( sys.path[0] )
import crv

def prex(cmd):
  myprocess = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  stdout,stderr = myprocess.communicate()
  myprocess.wait()                        
  return (myprocess.returncode,stdout,stderr)     

def short_jobid(long_jobid):
  sjid=long_jobid
  mo=re.match(r'(\d+)\.',long_jobid)
  if (mo):
    sjid=mo.group(1)
  return sjid

#parcing parameters
class crv_server:
  
  maxsessions=10
  qsub_template="""#!/bin/bash
# scrive log nella home utente
#PBS -l walltime=<CRV:WALLTIME>
#PBS -eo ~/.crv/<CRV:SID>.joblog
#PBS -q visual
#PBS -A cinstaff
#PBS -W group_list=cinstaff

. /cineca/prod/environment/module/3.1.6/none/init/bash
module purge
module use /plx/userprod/pro3dwe1/BA/modulefiles/profiles && module load luigi/advanced && module load autoload VirtualGL && module load TurboVNC
mkdir -p ~/.crv
vncserver -fg 2> ~/.crv/<CRV:SID>.vnclog
date
"""

  def __init__(self,pars):
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


  def execute(self):
    if (self.par_command == 'list'):
      self.execute_list()
    elif (self.par_command == 'new'):
      self.execute_new()
    elif (self.par_command == 'kill'):
      self.execute_kill()

  def get_jobs(self,U=False):
    (retval,stdout,stderr)=prex(['qstat','-f'])
    if (retval != 0 ) :
      sys.write.stderr(stderr);
      raise Exception( 'qstat returned non zero value: ' + str(retval) )
    else:
      r=re.compile('^Job Id:',re.MULTILINE)
      raw=r.split(stdout)
      raw.pop(0)                  #primo record vuoto
      if (U):
        ure='\w+'
      else:
        ure=self.par_u
      #tutti i job eventualmente dell'utente, running, sulla coda visual, con il nome del tipo crv-alphanum-num
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

  def load_sessions(self,U=False,sessionids=[]):
    if (U):
      udirs=glob.glob("/plx/user*/*/.crv")
      ure='\w+'
    else:
      udirs=[os.path.expanduser("~%s/.crv" % (self.par_u))]  
      ure=self.par_u

    #leggo le sessioni dai file
    r=re.compile(r'crv-(?P<sid>(?P<user>%s)-\d+)\.session$' % ure) 
    self.sessions={}
    for d in udirs:
      for f in os.listdir(d):
        ro= r.match(f)
        if ro:
          file= d + '/' + f
          user=ro.group(2)
          sid=ro.group(1)
          try:
            self.sessions[sid]=crv_session(fromfile=file)
          except:
            sys.stderr.write("WARNING: no valid session file: %s\n" % (file))
    #leggo sessioni dai job
    jobs=self.get_jobs(U=U)

    #setto attributo deletable
    for sid, ses in self.sessions.items():
      ses.deletable=0
      if sid in jobs.keys():
        job_jid=jobs[sid]
        file_jid=ses.hash['jobid']
        if ( job_jid == file_jid ):
          del(jobs[sid])
        else:
          sys.stderr.write('STRONG WARNING: session file of sid %s contain wrong jobid: %s (the running one is %s)\n' % (sid,file_jid,job_jid))
       else:
          ses.deletable=1
    
    #warning su job running ma senza file
    for sid, jid in jobs:
      sys.stderr.write("WARNING: found crv job with session %s without session file: %s\n" % (sid,jid)
      
#          ses.rank=short_jobid(jobid)

  def execute_list(self):
    self.load_sessions()
    
  def execute_new(self):
    self.load_sessions()
    """    sid=self.new_sid()
    file='%s/.crv/%s.session' % (self.u_home,sid)
    c=crv_session(state='init',sessionid=sid)
    c.serialize(file)
    jid=self.submit_job(sid)
    (n,d)self.wait_jobvnc(jid,10) 
    c=crv_session(state='run',node=n,display=d,jobid=jid,sessionid=sid,username=par_u)
    c.serialize(file)
    c.write(format)
    """

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
