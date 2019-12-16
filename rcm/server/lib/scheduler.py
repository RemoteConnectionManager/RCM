# std import

import logging
import re
import os
import sys
import stat
import pwd
import copy
from collections import OrderedDict

# local import
import plugin

logger = logging.getLogger('rcmServer' + '.' + __name__)

def convert_memory_to_megabytes(mem_string):
    #try:
        return {'G' : 1024, 'M' : 1}.get(mem_string[-1:], 0) * int(mem_string[:-1])
    #except:
        #return 0

def non_zero_min(a,b):
    # intended to return non zero min between two positive numbers
    if a and b:
        return min(a, b)
    else:
        return max(a, b)


class Scheduler(plugin.Plugin):

    def __init__(self, *args, **kwargs):
        if 'username' in kwargs:
            self.username = kwargs['username']
        else:
            self.username = pwd.getpwuid(os.geteuid())[0]
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
        #self.PARAMS['QUEUE'] = self.queues

    def all_accounts(self):
        raise NotImplementedError()

    def valid_accounts(self, **kwargs):
        raise NotImplementedError()

    def queues(self, **kwargs):
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
                         'scontrol': None,
                         'sacctmgr': None,
                         'squeue': None}
        super(SlurmScheduler, self).__init__(*args, **kwargs)
        #self._cluster_name = self.get_cluster_name()
        #self._qos = self.qos_info()
        #self._accounts = self.account_info()
        #self._partitions = self.partitions_info(['AllowQos', 'AllowAccounts', 'DenyAccounts', 'MaxTime', 'DefaultTime', 'MaxCPUsPerNode', 'MaxMemPerNode', 'QoS'])

    @property
    def cluster_name(self):
        try:
            return self._cluster_name
        except AttributeError:
            self._cluster_name = self.get_cluster_name()
            return self._cluster_name

    @property
    def accounts(self):
        try:
            return self._accounts
        except AttributeError:
            self._accounts = self.account_info()
            return self._accounts

    @property
    def qos(self):
        try:
            return self._qos
        except AttributeError:
            self._qos = self.qos_info()
            return self._qos

    @property
    def partitions(self):
        try:
            return self._partitions
        except AttributeError:
            self._partitions = self.partitions_info(['AllowQos', 'AllowAccounts', 'DenyAccounts', 'MaxTime', 'DefaultTime', 'MaxCPUsPerNode', 'MaxMemPerNode', 'QoS'])
            return self._partitions

    def get_cluster_name(self):
        cluster_name = ''
        scontrol = self.COMMANDS.get('scontrol', None)
        if scontrol:
            params = 'show config'.split(' ')
            raw_output = scontrol(*params,
                                output=str)
            cluster_match = re.search(r'ClusterName\s*=\s*(\w*)', raw_output)
            if cluster_match:
                cluster_name = cluster_match.group(1)
                self.logger.debug("computed cluster name:::>" + cluster_name + "<:::")
        return cluster_name


    def account_info(self):
        accounts = OrderedDict()
        try:
            sacctmgr = self.COMMANDS.get('sacctmgr', None)
            if sacctmgr:
                param_string = "show user " + self.username + " " + "withass where cluster=" + self.cluster_name + " " + "format=account%20,qos%120 -P"
                self.logger.debug("retrieving account and qos with command sacctmgr ::>" + param_string + "<::")
                params = param_string.split(' ')
                raw_output = sacctmgr(*params, output=str)
                for l in raw_output.splitlines()[1:]:
                    fields = l.split('|')
                    if fields[1]:
                        qos_list = fields[1].split(',')
                        if 'normal' in qos_list:
                            qos_list.remove('normal')
                            qos_list = ['normal'] + qos_list
                        accounts[fields[0]] = qos_list
            else:
                self.logger.warning("warning missing command sacctmgr:")
        except:
           pass
        return accounts

    def qos_info(self):
        qos = OrderedDict()
        sacctmgr = self.COMMANDS.get('sacctmgr', None)
        if sacctmgr:
            param_string = "show qos format=Name%20,MaxWall%20,MaxTRES%40,Flags%60,MaxTRESPerNode%60 -P"
            self.logger.debug("retrieving all qos info with command sacctmgr ::>" + param_string + "<::")
            params = param_string.split(' ')
            raw_output = sacctmgr(*params, output=str)
            for l in raw_output.splitlines()[1:]:
                try:
                    name,max_wall,max_tres,flags,max_tres_per_node = l.split('|')
                    qos[name] = {'max_wall': max_wall}
                    if max_tres:
                        for key_assign in max_tres.split(','):
                            key,val = key_assign.split('=')
                            qos[name]['max_' + key]  = val
                    if flags:
                        flags_list = flags.split(',')
                        for key in ['OverPartQOS']:
                            qos[name][key] = key in flags_list
                    if max_tres_per_node:
                        for key_assign in max_tres_per_node.split(','):
                            key,val = key_assign.split('=')
                            qos[name]['max_per_node_' + key]  = val

                except Exception as e:
                    self.logger.warning("Exception: " + str(e) + " in processing line:\n" + l)

        return qos

    def partitions_info(self,keywords):
        partitions = OrderedDict()
        scontrol = self.COMMANDS.get('scontrol', None)
        if scontrol:
            params = '--oneliner show partition'.split(' ')
            raw_output = scontrol(*params,
                                output=str)
            for l in raw_output.splitlines():
                partition_name_match = re.search(r'PartitionName\s*=\s*(\w*)', l)
                if partition_name_match:
                    partition_name = partition_name_match.group(1)
                    part_keys = OrderedDict()
                    for field in l.split(' '):
                        key,val = field.split('=',1)
                        if key in keywords:
                            part_keys[key] = val
                    partitions[partition_name] = part_keys

        sinfo = self.COMMANDS.get('sinfo', None)
        if sinfo:
            params = "-o %R|%l|%m|%c".split(' ')
            raw_output = sinfo(*params,
                               output=str)
            for l in raw_output.splitlines()[1:]:
                try:
                    partition = l.split('|')[0]
                    stringtime = l.split('|')[1]
                    if len(stringtime.split('-')) == 1:
                        time=stringtime
                    else:
                        time='23:59:59'
                    #memory = int(int(l.split('|')[2]) / 1000 * 0.90 )
                    memory_string = l.split('|')[2]+'M'
                    #cpu = int(l.split('|')[3])
                    cpu_string = l.split('|')[3]
                    if partitions[partition]['MaxTime'] != stringtime:
                        print("################## MaxTime ### ",partitions[partition]['MaxTime']," ####stringtime## ",stringtime)
                    if partitions[partition]['MaxMemPerNode'] == 'UNLIMITED':
                        partitions[partition]['MaxMemPerNode'] = memory_string
                    if partitions[partition]['MaxCPUsPerNode'] == 'UNLIMITED':
                        partitions[partition]['MaxCPUsPerNode'] = cpu_string
                except Exception as e:
                    self.logger.warning("Exception: " + str(e) + " in processing line:\n" + l)

        return partitions


    def allowed_accounts(self, partition):

        partition_info = self.partitions.get(partition, dict())
        deny_accounts = partition_info.get('DenyAccounts', '').split(',')
        allow_accounts_string = partition_info.get('AllowAccounts', 'ALL')
        if allow_accounts_string == 'ALL':
            allow_accounts_list = list(self.accounts.keys())
        else:
            allow_accounts_list = allow_accounts_string.split(',')
        ok_accounts = []
        for a in self.accounts.keys():
            if a in allow_accounts_list and not a in deny_accounts:
                ok_accounts.append(a)
        return ok_accounts


    def allowed_qos(self, partition):

        partition_info = self.partitions.get(partition, dict())
        allow_qos_string = partition_info.get('AllowQos', 'ALL')
        if allow_qos_string == 'ALL':
            allow_qos_list = list(self.qos.keys())
        else:
            allow_qos_list = allow_qos_string.split(',')
        ok_qos = []
        for q in self.qos.keys():
            if q in allow_qos_list:
                ok_qos.append(q)
        return ok_qos

    def partition_schema(self, partition, account, **kwargs):
        """

        :param partition: name of the partition to produce the default schema for
        :param account:  name of the account
        :param kwargs:
        :return: OrderedDict of default schema for the partition, if the dict is void, partiton can not be selected, option not shown
        """
        allowed_accounts = self.allowed_accounts(partition)
        partition_qos = self.allowed_qos(partition)
        partitition_schema = kwargs.get('default_params', OrderedDict())
        qos_defaults = partitition_schema.get('QOS', OrderedDict())
        if account in allowed_accounts:
            account_qos = self.accounts.get(account,[])
            valid_qos = OrderedDict()
            for qos in account_qos:
                if qos in partition_qos:
                    # use deepcopy to avoid pollute original input dict
                    qos_parameters = copy.deepcopy(qos_defaults.get(qos, qos_defaults.get('ALL', OrderedDict())))

                    stringtime = ''
                    max_node_memory_for_partition = convert_memory_to_megabytes(self.partitions.get(partition, dict()).get('MaxMemPerNode', '0M'))
                    max_node_cpu_for_partition = int(self.partitions.get(partition, dict()).get('MaxCPUsPerNode', '0'))
                    partition_specific_qos_data = self.qos.get(self.partitions.get(partition, dict()).get('QoS', ''),dict())
                    max_memory_per_node_for_partition_qos = convert_memory_to_megabytes(partition_specific_qos_data.get('max_per_node_mem','0M'))
                    max_cpu_per_node_for_partition_qos = int(partition_specific_qos_data.get('max_per_node_cpu','0'))
                    max_memory_for_partition_qos = convert_memory_to_megabytes(partition_specific_qos_data.get('max_mem','0M'))
                    max_cpu_for_partition_qos = int(partition_specific_qos_data.get('max_cpu','0'))

                    max_memory = non_zero_min(non_zero_min(max_node_memory_for_partition, max_memory_per_node_for_partition_qos), max_memory_for_partition_qos)
                    max_cpu = non_zero_min(non_zero_min(max_node_cpu_for_partition, max_cpu_per_node_for_partition_qos), max_cpu_for_partition_qos)


                    if self.qos.get(qos,dict()).get('OverPartQOS', False):
                        stringtime = self.qos.get(qos,dict()).get('max_wall', '')
                        max_memory_for_qos = convert_memory_to_megabytes(self.qos.get(qos,dict()).get('max_mem','0M'))
                        max_memory = non_zero_min(max_memory, max_memory_for_qos)
                        max_cpu_for_qos = int(self.qos.get(qos,dict()).get('max_cpu','0'))
                        max_cpu = non_zero_min(max_cpu, max_cpu_for_qos)

                    if not stringtime:
                        stringtime = self.partitions.get(partition, dict()).get('MaxTime','')
                    if len(stringtime.split('-')) == 1:
                        max_time=stringtime
                    else:
                        max_time='23:59:59'

                    if max_time : qos_parameters['TIME'] = {'max' : max_time}
                    if max_memory : qos_parameters['MEMORY'] = {'max' : int(max_memory / 1024)}
                    if max_cpu : qos_parameters['CPU'] = {'max' : max_cpu}
                    valid_qos[qos] = qos_parameters
            if valid_qos:
                partitition_schema['QOS'] =  valid_qos
        return partitition_schema

    def valid_accounts(self, **kwargs):
        out_schema = OrderedDict()
        default_params = kwargs.get('default_params', dict())
        for account in self.accounts:
            partitions_default_params = default_params.get(account, default_params.get('ALL', OrderedDict())).get('QUEUE', OrderedDict())
            partitions_schema = OrderedDict()
            for partition in self.partitions:
                part_default_params = partitions_default_params.get(partition, partitions_default_params.get('ALL', dict()))
                if part_default_params:
                    partition_schema = self.partition_schema(partition,account, default_params=copy.deepcopy(part_default_params))
                else:
                    partition_schema = self.partition_schema(partition,account)
                if partition_schema:
                    partitions_schema[partition] = partition_schema
            if partitions_schema :
                out_schema[account] = {'QUEUE' : partitions_schema}
        return out_schema



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
