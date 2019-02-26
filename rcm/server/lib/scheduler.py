# std import
import copy
import logging
from collections import OrderedDict

# local import
import jobscript_builder
import plugin
import utils

logger = logging.getLogger('rcmServer')

#
# class Scheduler(jobscript_builder.ManagedChoiceNode):
#     NAME = None
#
#     def __init__(self, *args, **kwargs):
#         """
#         General scheduler class,
#         :param schema: accept a schema to override schema that are retrieved through CascadeYamlConfig singleton
#         """
#         self.is_working = False
#
#         merged_defaults = copy.deepcopy(kwargs['defaults'])
#         if merged_defaults == None:
#             merged_defaults = OrderedDict()
#         for param in ['ACCOUNT', 'QUEUE']:
#             if param in kwargs:
#                 logger.debug("---------------------------------")
#                 merged_defaults[param] = self.merge_list(merged_defaults.get(param, OrderedDict()),
#                                                          kwargs.get(param, []))
#                 del kwargs[param]
#         kwargs['defaults'] = merged_defaults
#         super(Scheduler, self).__init__(*args, **kwargs)
#
#     @staticmethod
#     def merge_list(preset, computed):
#         logger.debug("merging:" + str(preset) + "----" + str(computed))
#         out = copy.deepcopy(preset)
#         for a in computed:
#             if a not in out:
#                 if hasattr(out, 'append'):
#                     out.append(a)
#                 else:
#                     out[a] = OrderedDict()
#         logger.debug("merged:" + str(out))
#         return out


class BatchScheduler(plugin.Plugin):

    COMMANDS = {}

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
    NAME = 'PBS'
    COMMANDS = {'qstat': None,
                'non_existing_command': None}


class LocalScheduler(plugin.Plugin):
    NAME = 'Local'


class OSScheduler(plugin.Plugin):
    NAME = 'SSH'


class SlurmScheduler(BatchScheduler):
    NAME = 'Slurm'
    COMMANDS = {'sshare': None,
                'sinfo': None}

    def __init__(self, *args, **kwargs):
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
