# stdlib
import json
import sys
import os
import copy
import glob
from collections import OrderedDict

root_rcm_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_rcm_path)

import utils


class CascadeYamlConfig:
    """
    singleton ( pattern from https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html )
    config class that parse cascading yaml files with hiyapyco
    constructor take a list of files that are parsed hierachically by parse method
    """

    class __CascadeYamlConfig:
        def __init__(self, list_paths=None):
            self._conf = OrderedDict()
            if list_paths:
                self.list_paths = list_paths
            else:
                self.list_paths = glob.glob(os.path.join(os.path.dirname(os.path.realpath(__file__)), "*.yaml"))

        def parse(self):
            print("CascadeYamlConfig: parsing: ", self.list_paths)
            if self.list_paths:
                self._conf = utils.hiyapyco.load(
                    *self.list_paths,
                    interpolate=True,
                    method=utils.hiyapyco.METHOD_MERGE,
                    failonmissingfiles=False
                )

        @property
        def conf(self):
            print("Getting value")
            return copy.deepcopy(self._conf)

        def __getitem__(self, nested_key_list=None):
            """
            this funchion access parsed config as loaded from hiyapyco
            :param nested_key_list: list of the nested keys to retrieve
            :return: deep copy of OrderedDict
            """
            val = self._conf
            if nested_key_list:
                for k in nested_key_list:
                    val = val.get(k, OrderedDict())
            return copy.deepcopy(val)


    instance = None

    def __init__(self, listpaths=None):
        if not CascadeYamlConfig.instance:
            CascadeYamlConfig.instance = CascadeYamlConfig.__CascadeYamlConfig(listpaths)
            CascadeYamlConfig.instance.parse()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __getitem__(self, nested_key_list):
        return self.instance.__getitem__(nested_key_list)

class BaseGuiComposer(object):
    NAME = None

    def __init__(self, schema=None, name=None):
        if schema:
            self.schema = schema
        else:
            if name:
                self.NAME = name
            #self.schema = CascadeYamlConfig().get_copy(['defaults', self.NAME])
            self.schema = CascadeYamlConfig()['defaults', self.NAME]


class LeafGuiComposer(BaseGuiComposer):

    def get_gui_options(self):
        return self.schema


class CompositeComposer(BaseGuiComposer):

    def __init__(self, name=None):
        super(CompositeComposer, self).__init__(name=name)
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def get_gui_options(self):
        options = OrderedDict()
        for child in self.children:
            options[child.NAME] = child.get_gui_options()
        return options


class ChoiceGuiComposer(CompositeComposer):

    def get_gui_options(self):
        composer_options = self.schema
        composer_choice = OrderedDict()
        if self.children:
            for child in self.children:
                composer_choice[child.NAME] = child.get_gui_options()
            composer_options['choices'] = composer_choice
        if 'list' in composer_options :
            del composer_options['list']
        return composer_options


class BaseScheduler(object):
    """
    Base scheduler class, pattern taken form https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Factory.html
    """
    NAME = None

    def __init__(self, schema=None):
        """
        General scheduler class,
        :param schema: accept a schema to override defaults that are retrieved through CascadeYamlConfig singleton
        """
        if self.preset():
            self.working = True
        else:
            self.working = False

        if schema:
            self.schema = schema
        else:
            self.schema = CascadeYamlConfig()['defaults', 'SCHEDULER']

    def get_gui_options(self, accounts=None, queues=None):
        print("preset--->",self.preset())
        if not accounts:
            accounts = self.preset().get('ACCOUNT', [])

        queue_preset = self.preset().get('QUEUE', OrderedDict())
        if not queues:
            queues = queue_preset
        print("accounts: ", accounts)
        print("queues  : ", queue_preset)
        out = {'list': copy.deepcopy(self.schema.get('list', OrderedDict()))}
        if queues:
            queue_schema = copy.deepcopy(self.schema['list']['QUEUE'])
            queue_choices = OrderedDict()
            for q in queues:
                # print(q,queue_preset[q])
                l = copy.deepcopy(queue_schema['list'])
                if queue_preset.get(q, dict()):
                    for w in queue_preset.get(q, dict()):
                        print(w, queue_preset[q][w])
                        for m in queue_preset[q][w]:
                            l[w]['values'][m] = queue_preset[q][w][m]
                queue_choices[q] = {'list': l}
            queue_schema['choices'] = queue_choices
            if 'list' in queue_schema:
                del queue_schema['list']
            out['list']['QUEUE'] = queue_schema
        else:
            del out['list']['QUEUE']
        if accounts:
            out['list']['ACCOUNT']['values'] = accounts
        else:
            del out['list']['ACCOUNT']
        if not out['list']:
            del out['list']

        return out

    @classmethod
    def preset(cls):
        """
        This retrieve the specific preset for the scheduler from the config singleton based on scheduler NAME
        :return: return the preset nested OrderedDict from specific key, see test yaml files
        """
        if cls.NAME:
            #return  CascadeYamlConfig().get_copy(['composites','schedulers', cls.NAME])

            return CascadeYamlConfig()['composites', 'SCHEDULER', cls.NAME]


class SlurmScheduler(BaseScheduler):
    NAME = 'Slurm'

    def __init__(self, schema=None):
        super(SlurmScheduler, self).__init__(schema=schema)
        # super().__init__(schema=schema)
        # BaseScheduler.__init__(self,schema=schema)
        self.commands = {'sshare': None, 'sinfo': None}

        for c in self.commands:
            exe = utils.which(c)
            if exe:
                self.commands[c] = exe
            else:
                self.working = self.working and False
                print("command: ", c, " Not Found")

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
            if self.validate_account(a): accounts.append(a)
        return accounts

    def get_queues(self):
        # hints on useful slurm commands
        # sacctmgr show qos
        sinfo = self.commands.get('sinfo', None)
        if sinfo:
            out = sinfo(
                '--format=%P',
                output=str
            )
            partitions = []
            for l in out.splitlines()[1:]:
                partitions.append(l)
            return partitions
        else:
            return []

    def get_gui_options(self, accounts=[], queues=[]):
        return super(SlurmScheduler, self).get_gui_options(accounts=self.valid_accounts(), queues=self.get_queues())


class PBSScheduler(BaseScheduler):
    NAME = 'PBS'


class LocalScheduler(BaseScheduler):
    NAME = 'Local'


class SSHScheduler(BaseScheduler):
    NAME = 'SSH'


class SchedulerManager(ChoiceGuiComposer):
    NAME = 'SCHEDULER'
    SCHEDULERS = [SlurmScheduler, PBSScheduler, LocalScheduler]

    def __init__(self):
        super(SchedulerManager, self).__init__()
        for sched_class in self.SCHEDULERS:
            sched = sched_class()
            if sched.working:
                self.add_child(sched)


if __name__ == '__main__':
    config = CascadeYamlConfig()

    schedulers = SchedulerManager()
    root = CompositeComposer()
    root.add_child(schedulers)
    root.add_child(LeafGuiComposer(name='DIVIDER'))
    root.add_child(ChoiceGuiComposer(name='SESSION'))
    out = root.get_gui_options()
    # out=sched.get_gui_options(accounts=['minnie','clarabella'],queues=['prima_coda_indefinita','gll_user_prd'])
    print("Root-->" + json.dumps(out, indent=4))
