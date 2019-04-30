# std import

import logging
import re
import os
import sys
import stat

# local import
import plugin

logger = logging.getLogger('rcmServer' + '.' + __name__)


class Scheduler(plugin.Plugin):

    def __init__(self, *args, **kwargs):
        super(Scheduler, self).__init__()

    def submit(self, script='', jobfile=''):
        raise NotImplementedError()

    def get_user_jobs(self, username=''):
        raise NotImplementedError()

    def kill_job(self, jobid=''):
        raise NotImplementedError()

    def handled(self, jobid=''):
        return True

    def generic_submit(self, script='', jobfile='', batch_command='/bin/batch', jobfile_executable=True):

        if jobfile:
            if script:
                with open(jobfile, 'w') as f:
                    f.write(script)
            if jobfile_executable:
                os.chmod(jobfile, stat.S_IRWXU)
            self.logger.info(self.__class__.__name__ + " " + self.NAME + " submitting " + jobfile)

            batch = self.COMMANDS.get(batch_command, None)
            if batch:
                raw_output = batch(jobfile,
                                   output=str)
                self.logger.debug("generic_submit raw_output: " + raw_output)
                jobid_regex = self.templates.get('JOBID_REGEX', "Submitted  (\d*)")
                self.logger.debug("generic_submit jobid_regex " + jobid_regex)
                r = re.match(jobid_regex, raw_output)
                if (r):
                    jobid = r.group(1)
                    self.logger.info("scheduler: " + self.NAME + " jobid: " + str(jobid))
                    return jobid
                else:
                    raise Exception("Unable to extract jobid from output: %s" % raw_output)
        return None


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

    def __init__(self, *args, **kwargs):
        self.NAME = 'PBS'
        self.COMMANDS = {'qstat': None,
                    'non_existing_command': None}
        super(PBSScheduler, self).__init__(*args, **kwargs)



class OSScheduler(Scheduler):

    def __init__(self, *args, **kwargs):
        self.NAME = 'SSH'
        self.COMMANDS = {'/bin/bash': None,
                         'ps': None,
                         'kill': None}
        super(OSScheduler, self).__init__(*args, **kwargs)
        if 'node' in kwargs:
            self.prefix = kwargs['node'].split('.')[0] + '.'
        else:
            self.prefix = ''

    def submit(self, script='', jobfile=''):
        processid = self.generic_submit(script=script, jobfile=jobfile, batch_command='/bin/bash')
        if processid:
            return self.prefix + str(processid)
        else:
            return ''

    def get_user_jobs(self, username=''):
        ps = self.COMMANDS.get('ps', None)
        if ps:
            params = []
            if username:
                params.extend(('-u ' + username).split(' '))
            self.logger.debug("params " + str(params))
            raw_output = ps(*params,
                            output=str)

            raw = filter(None, raw_output.split('\n'))

            jobs = {}
            for jline in raw:
                processid = jline.lstrip().split(' ')[0]
                jid = self.prefix + str(processid)
                self.logger.debug("job_id " + str(jid))
                jobs[jid] = jline
            return jobs

    def kill_job(self, jobid=''):
        """
        kill the process that has been launched ( jobid ) and all it's children,
        by grabbing the group id and calling kill with -gid /list display remote sessions.
        https://stackoverflow.com/questions/392022/whats-the-best-way-to-send-a-signal-to-all-members-of-a-process-group/15139734#15139734
        """

        self.logger.debug("Scheduler: " + self.NAME + "asked to kill_job: " + jobid)
        processid = jobid.split('.')[-1:][0]
        if processid:
            try:
                ps = self.COMMANDS.get('ps', None)
                if ps:
                    params = ['opgid=', str(processid)]
                    process_group = ps(*params, output=str).strip()
                    logger.debug("killing process_group: " + process_group)
                    kill = self.COMMANDS.get('kill', None)
                    # it seems that in order to kill all process of a group, prepend the group with -
                    params = ['-TERM', '-' + process_group]
                    out = kill(*params, output=str)
                    return True
            except:
                sys.stderr.write("Can not kill  process with pid: %s." % processid)
        return False

    def handled(self, jobid=''):
        jobid_nodename = jobid.split('.')[0]
        prefix_nodename = self.prefix.split('.')[0]
        return jobid_nodename == prefix_nodename


class SlurmScheduler(BatchScheduler):

    def __init__(self, *args, **kwargs):
        self.NAME = 'Slurm'
        self.COMMANDS = {'sshare': None,
                         'sinfo': None,
                         'sbatch': None,
                         'scancel': None,
                         'squeue': None}
        super(SlurmScheduler, self).__init__(*args, **kwargs)

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
            self.logger.debug("warning missing command sshare:")
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
        self.logger.debug("Slurm get queues")
        sinfo = self.COMMANDS.get('sinfo', None)
        if sinfo:
            raw_output = sinfo('--format=%R',
                               output=str)
            partitions = []
            for l in raw_output.splitlines()[1:]:
                partitions.append(l)
            self.logger.debug("Slurm found queues: " + str(partitions))
            return partitions
        else:
            self.logger.debug("warning missing command sinfo:")
            return []

    def submit(self, script='', jobfile=''):
        return self.generic_submit(script=script, jobfile=jobfile, batch_command='sbatch')

    def get_user_jobs(self, username=''):
        squeue = self.COMMANDS.get('squeue', None)
        if squeue:
            params = '-o %i#%t#%j#%a -h -a'.split(' ')
            if username:
                params.extend(('-u ' + username).split(' '))
                self.logger.debug("squeue params " + str(params))
            raw_output = squeue(*params,
                                output=str)

            check_rcm_job_string = self.NAME
            raw = raw_output.split('\n')
            # logger.debug("raw output lines:\n" + str(raw))
            jobs = {}
            for j in raw:
                self.logger.debug("jobline: " + str(j))
                mo = j.split('#')
                self.logger.debug("mo split #" + str(len(mo)) + " " + ' '.join(str(p) for p in mo))
                if len(mo) == 4 and check_rcm_job_string in mo[2]:
                    sid = mo[0]
                    jobs[sid] = mo[2]
            return jobs

    def kill_job(self, jobid=''):
        self.logger.debug("Scheduler: " + self.NAME + "asked to kill_job: " + jobid)
        if jobid:
            try:
                scancel = self.COMMANDS.get('scancel', None)
                if scancel:
                    params = [str(jobid)]
                    out = scancel(*params, output=str)
                    self.logger.debug("removed job: " + str(jobid) + " output:\n" + out)
                    return True
            except Exception as e:
                self.logger.warning("Exception: " + str(e) + " in killing job " + str(jobid))
                sys.stderr.write("Can not kill  job: %s." % jobid)
        return False
