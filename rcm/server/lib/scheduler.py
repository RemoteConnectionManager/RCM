# std import
import copy
import logging
from collections import OrderedDict
import re
import subprocess
import os
import stat

# local import
import jobscript_builder
import plugin
import utils

logger = logging.getLogger('rcmServer')

class Scheduler(plugin.Plugin):

    def __init__(self, *args, **kwargs):
        super(Scheduler, self).__init__(*args, **kwargs)

    def submit(self, script='', jobfile=''):
        raise NotImplementedError()



class BatchScheduler(Scheduler):

    def __init__(self, *args, **kwargs):
        super(BatchScheduler, self).__init__(*args, **kwargs)
        self.PARAMS['ACCOUNT'] = self.valid_accounts
        self.PARAMS['QUEUE'] = self.queues

    def all_accounts(self):
        raise NotImplementedError()

    def valid_accounts(self):
        raise NotImplementedError()

    def queues(self):
        raise NotImplementedError()



class PBSScheduler(BatchScheduler):

    COMMANDS = {'qstat': None,
                'non_existing_command': None}

    def __init__(self, *args, **kwargs):
        super(PBSScheduler, self).__init__(*args, **kwargs)
        self.NAME = 'PBS'


class OSScheduler(Scheduler):

    def __init__(self, *args, **kwargs):
        super(OSScheduler, self).__init__(*args, **kwargs)
        self.NAME = 'SSH'

    def submit(self, script='', jobfile=''):
        logger.info(self.__class__.__name__ + " " + self.NAME + " submitting " + jobfile)
        for t in self.templates:
            print("############ ", t)

        if jobfile:
            if script:
                with open(jobfile, 'w') as f:
                    f.write(script)
            os.chmod(jobfile, stat.S_IRWXU)

            print("Submitting job file:", jobfile)
            pid = subprocess.Popen(['/bin/bash', os.path.realpath(jobfile)], close_fds=True).pid
            return pid

class SlurmScheduler(BatchScheduler):

    COMMANDS = {'sshare': None,
                'sinfo': None,
                'sbatch': None}

    def __init__(self, *args, **kwargs):
        super(SlurmScheduler, self).__init__(*args, **kwargs)
        self.NAME = 'Slurm'

    def all_accounts(self):
        # sshare --parsable -a
        # Eric: sshare --parsable --format %
        # saldo -b
        # Lstat.py
        sshare = self.COMMANDS.get('sshare', None)
        if sshare:
            out = sshare(
                '--parsable',
                output=str
            )
            accounts = []
            for l in out.splitlines()[1:]:
                accounts.append(l.split('|')[0])
            return accounts
        else:
            return []


    def validate_account(self, account):
        return True

    def valid_accounts(self):
        accounts = []
        for a in self.all_accounts():
            if self.validate_account(a):
                accounts.append(a)
        return accounts

    def queues(self):
        # hints on useful slurm commands
        # sacctmgr show qos
        logger.debug("Slurm get queues !!!!")
        sinfo = self.COMMANDS.get('sinfo', None)
        if sinfo:
            raw_output = sinfo('--format=%R',
                               output=str)
            partitions = []
            for l in raw_output.splitlines()[1:]:
                partitions.append(l)
            logger.debug("Slurm found queues:" + str(partitions) + "!!!!")
            return partitions
        else:
            logger.debug("warning !!!!!! sinfo:" + str(sinfo))
            return []

    def submit(self, script='', jobfile=''):

        if jobfile:
            if script:
                with open(jobfile, 'w') as f:
                    f.write(script)

            logger.info(self.__class__.__name__ + " " + self.NAME + " submitting " + jobfile)

            sbatch = self.COMMANDS.get('sbatch', None)
            if sbatch:
                raw_output = sbatch(jobfile,
                                    output=str)
                logger.debug("@@@@@@@@@@@@@@ raw_output: " + raw_output)
                jobid_regex = self.templates.get('JOBID_REGEX', "Submitted  (\d*)")
                logger.debug("@@@@@@@@@@@@@ jobid_regex " + jobid_regex)
                r=re.match(jobid_regex, raw_output)
                if (r):
                    return r.group(1)
                else:
                    raise Exception("Unable to extract jobid from output: %s" % (raw_output))




