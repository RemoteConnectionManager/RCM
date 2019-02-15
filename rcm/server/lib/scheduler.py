# std import
import copy
import logging
from collections import OrderedDict

# local import
import jobscript_builder
import utils

logger = logging.getLogger('rcmServer')


class Scheduler(jobscript_builder.ManagedChoiceNode):
    NAME = None

    def __init__(self, *args, **kwargs):
        """
        General scheduler class,
        :param schema: accept a schema to override schema that are retrieved through CascadeYamlConfig singleton
        """
        merged_defaults = copy.deepcopy(kwargs['defaults'])
        if merged_defaults == None:
            merged_defaults = OrderedDict()
        for param in ['ACCOUNT', 'QUEUE']:
            if param in kwargs:
                logger.debug("---------------------------------")
                merged_defaults[param] = self.merge_list(merged_defaults.get(param, OrderedDict()),
                                                         kwargs.get(param, []))
                del kwargs[param]
        kwargs['defaults'] = merged_defaults
        super(Scheduler, self).__init__(*args, **kwargs)

    @staticmethod
    def merge_list(preset, computed):
        logger.debug("merging:" + str(preset) + "----" + str(computed))
        out = copy.deepcopy(preset)
        for a in computed:
            if a not in out:
                if hasattr(out, 'append'):
                    out.append(a)
                else:
                    out[a] = OrderedDict()
        logger.debug("merged:" + str(out))
        return out


class BatchScheduler(Scheduler):

    commands = {}

    def __init__(self, *args, **kwargs):
        for c in self.commands:
            exe = utils.which(c)
            if exe:
                self.commands[c] = exe
                logger.debug("command: " + c + " Found !!!!")
            else:
                self.working = self.working and False
                logger.debug("command: " + c + " Not Found !!!!")
        kwargs['ACCOUNT'] = self.valid_accounts()
        kwargs['QUEUE'] = self.get_queues()
        super(BatchScheduler, self).__init__(*args, **kwargs)

    def valid_accounts(self):
        return ['dummy_account_1', 'dummy_account_2']

    def get_queues(self):
        return ['dummy_queue_1', 'dummy_queue_2']


class PBSScheduler(BatchScheduler):
    NAME = 'PBS'


class LocalScheduler(Scheduler):
    NAME = 'Local'


class OSScheduler(Scheduler):
    NAME = 'SSH'


class SlurmScheduler(BatchScheduler):
    NAME = 'Slurm'
    commands = {'sshare': None, 'sinfo': None}

    def __init__(self, *args, **kwargs):
        # super().__init__(schema=schema)
        # BaseScheduler.__init__(self,schema=schema)
        # self.commands = {'sshare': None, 'sinfo': None}
        super(SlurmScheduler, self).__init__(*args, **kwargs)

    def get_all_accounts(self):
        # sshare --parsable -a
        # Eric: sshare --parsable --format %
        # saldo -b
        # Lstat.py
        sshare = self.commands.get('sshare', None)
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
        for a in self.get_all_accounts():
            if self.validate_account(a):
                accounts.append(a)
        return accounts

    def get_queues(self):
        # hints on useful slurm commands
        # sacctmgr show qos
        logger.debug("Slurm get queues !!!!")
        sinfo = self.commands.get('sinfo', None)
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
