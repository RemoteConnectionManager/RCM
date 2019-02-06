# stdlib

import logging

from utils.scheduler_base import *

logger = logging.getLogger('RCM.composer')



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


