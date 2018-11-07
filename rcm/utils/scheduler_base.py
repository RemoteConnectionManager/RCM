# stdlib
import logging
import copy
from collections import OrderedDict


from utils.jobscript_composer_base import *

logger = logging.getLogger('RCM.composer')


class BaseScheduler(ManagedChoiceGuiComposer):
    """
    Base scheduler class, pattern taken form https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Factory.html
    """
    NAME = None

    def __init__(self, *args, **kwargs):
        """
        General scheduler class,
        :param schema: accept a schema to override schema that are retrieved through CascadeYamlConfig singleton
        """
        merged_defaults = copy.deepcopy(kwargs['defaults'])
        for param in ['ACCOUNT', 'QUEUE']:
            if param in kwargs:
                logger.debug("---------------------------------")
                merged_defaults[param] = self.merge_list(merged_defaults.get(param, OrderedDict()),
                                                         kwargs.get(param, []))
                del kwargs[param]
        kwargs['defaults'] = merged_defaults
        super(BaseScheduler, self).__init__(*args, **kwargs)

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


class BatchScheduler(BaseScheduler):

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


class SchedulerManager(ManagerChoiceGuiComposer):
    NAME = 'SCHEDULER'
    SCHEDULERS = []

    def __init__(self, *args, **kwargs):
        super(SchedulerManager, self).__init__(*args, **kwargs)
        logger.debug("########### schedulers:" + str(self.SCHEDULERS))
        if 'list' in self.schema:
            for class_name in self.defaults:
                logger.debug("handling child  : " + class_name)
                managed_class = ManagedChoiceGuiComposer
                for sched_class in self.SCHEDULERS:
                    if sched_class.NAME == class_name:
                        managed_class = sched_class
                        break
                child = managed_class(name=class_name,
                                      schema=copy.deepcopy(self.schema['list']),
                                      defaults=copy.deepcopy(self.defaults.get(class_name, OrderedDict())))
                if child.working:
                    self.add_child(child)


    @classmethod
    def register_scheduler(cls, sched_class_list):
        logger.debug("#### setting class " + str(cls) + " to " +  str(sched_class_list))
        for sched_class in sched_class_list:
            if sched_class not in  cls.SCHEDULERS:
                cls.SCHEDULERS.append(sched_class)