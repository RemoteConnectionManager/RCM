#import os.path
import os
import sys
import shlex, subprocess
import re
import glob
import string
import time
import datetime
import logging
import rcm_base_server
import json
class rcm_server(rcm_base_server.rcm_base_server):
      
      def vnc_command_in_background(self): 
          logger = logging.getLogger("basic")    
          logger.debug("vnc_command_in_background")
          return False

      # get group to be used submitting a job
      def getQueueGroup(self,queue): 
          logger = logging.getLogger("basic")    
          logger.debug("getQueueGroup")
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

      def prex(self,cmd): 
          logger = logging.getLogger("basic")    
          logger.debug("prex")
          cmdstring=cmd[0]
          for p in cmd[1:]:
                cmdstring+=" '%s'" % (p) 
          #sys.stderr.write("Executing: %s\n" % (cmdstring)  )
          logger.debug("Popen cmd"+str(cmd))
          myprocess = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
          stdout,stderr = myprocess.communicate()
          myprocess.wait()                        
          return (myprocess.returncode,stdout,stderr)     
        
      def cprex(self,cmd): 
          logger = logging.getLogger("basic")    
          logger.debug("cprex")
          (r,o,e)=self.prex(cmd)
          if (r != 0):
                print e
                raise Exception("command %s failed with error: %s" % ([cmd[0],cmd[-1]],e))
          return (r,o,e)

      # submit a PBS job
      def submit_job(self,sid,rcm_dirs,jobScript): 
          logger = logging.getLogger("basic")    
          logger.debug("submit_job")
          #icineca deployment dependencies
          self.qsub_template=jobScript
          #self.qsub_template="""#!/bin/bash


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

          group=os.environ.get('ACCOUNT_NUMBER',os.path.basename(os.environ.get('WORK','')))

          #group = self.getQueueGroup(self.queue) 
            
          #For reserved queue set only "select=1"   
          queueParameter = "select=1"
          if(not self.queue.startswith('R')):
                queueParameter += ":Qlist=" + self.queue + ":viscons=1"
          self.substitutions['RCM_QUEUEPARAMETER']=queueParameter
          
          self.substitutions['RCM_DIRECTIVE_A'] = self.groupSubstitution(group,'#PBS -A $RCM_GROUP')
          self.substitutions['RCM_QSUBPAR_A'] = self.groupSubstitution(group,'-A $RCM_GROUP')

          #Industrial users do not have to use -W group_list
          if( self.username.startswith('a06',0,3) ):
                self.substitutions['RCM_DIRECTIVE_W'] = ''
          else:
                self.substitutions['RCM_DIRECTIVE_W'] = self.groupSubstitution(group,'#PBS -W group_list=$RCM_GROUP')

          batch=s.safe_substitute(self.substitutions)
          print "batch------------------------\n",batch
          f=open(file,'w')
          f.write(batch)
          f.close()
          logger.debug("----- sbatch args "+" "+otp+" "+file)
          (res,out,err)=self.cprex(['sbatch','--export=RCM_OTP_FILE='+otp,file])
          logger.debug("Popen submit : " + str(res)+" \n"+out+" \n"+err)
          r=re.match(r"Submitted batch job (\d*)",out)
          if (r):
                return r.group(1)
          else:
                raise Exception("Unknown qsub output: %s" % (out))

        # kill a PBS job
      def kill_job(self,jid): 
          logger = logging.getLogger("basic")    
          logger.debug("kill_job")
          self.cprex(['scancel',jid])
          
          
      # get available queues for the user
      def get_queue(self,testJobScriptDict=None): 
          logger = logging.getLogger("basic")    
          logger.debug("get_queue")
          group=os.environ.get('ACCOUNT_NUMBER',os.path.basename(os.environ.get('WORK','')))
          logger.debug("OOOOOOOO"+group)
          self.substitutions['RCM_QSUBPAR_A'] = self.groupSubstitution(group,'--account=$RCM_GROUP')
          logger.debug("SUB"+self.substitutions['RCM_QSUBPAR_A'])
          #get list of possible queue (named "visual")
          queueList = []
          if(not testJobScriptDict): testJobScriptDict=self.pconfig.get_testjobs()
          logger.debug("OOOOOO TJD = "+json.dumps(testJobScriptDict))
          for key, value in testJobScriptDict.iteritems():
                logger.debug(key)
                logger.debug(value)
                args = shlex.split(string.Template(value).safe_substitute(self.substitutions))
                logger.debug("OOOOOOO TEST job = "+' '.join(str(p) for p in args))
                p1 = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout,stderr=p1.communicate()
                logger.debug("OOOOOOO "+"\n stdout :"+stdout+"\n stderr"+stderr)
                regex_string = r"Submitted batch job (\d*)"
                m = re.search(regex_string, stdout)
                if m:
                  queueList.append(key)
                  self.kill_job(m.group(1))
          
          return queueList

      def get_jobs(self, U=False):
          logger = logging.getLogger("basic")    
          logger.debug("get_jobs")
          (retval,stdout,stderr)=self.prex(['squeue', '-o %i#%t#%j#%a','-h','-p','bdw_all_rcm','-u',self.username])
          logger.debug("squeue output: "+str(retval)+" \n"+str(stdout)+" \n"+str(stderr))
          
          check_rcm_job_string = self.username+"-slurm"
          logger.debug("check_rcm_job_string "+check_rcm_job_string)

          if (retval != 0 ) :
                logger.debug("retval no 0")
                sys.stderr.write(stderr);
                raise Exception( 'squeue returned non zero value: ' + str(retval) )
          else:
                raw=stdout.split('\n')
                logger.debug("raw"+str(type(raw)))
                jobs={}
                for j in raw:
                      logger.debug("j"+str(j))
                      mo=j.split('#')
                      logger.debug("mo split #"+str(len(mo))+" "+' '.join(str(p) for p in mo))
                      if  len(mo) == 4 and check_rcm_job_string in mo[2]: 
                         sid=mo[2]
                         jobs[sid]=mo[0]
                return(jobs)

