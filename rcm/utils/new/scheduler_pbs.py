# stdlib
import sys
import os
import logging
import json
import copy
import glob
from collections import OrderedDict

root_rcm_path = os.path.dirname((os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_rcm_path)

import utils


logger = logging.getLogger('RCM.composer')


class PBSScheduler(BatchScheduler):
    NAME = 'PBS'
    # commands = {'qstat': None}


class LocalScheduler(BaseScheduler):
    NAME = 'Local'


class SSHScheduler(BaseScheduler):
    NAME = 'SSH'


class SchedulerManager(ManagerChoiceGuiComposer):
    NAME = 'SCHEDULER'
    SCHEDULERS = [SlurmScheduler, PBSScheduler, LocalScheduler]

    def __init__(self, *args, **kwargs):
        super(SchedulerManager, self).__init__(*args, **kwargs)
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


if __name__ == '__main__':

    config = CascadeYamlConfig()
    logger.setLevel(logging.INFO)
    root = AutoChoiceGuiComposer(schema=config.conf['schema'],
                                 defaults=config.conf['defaults'],
                                 class_table={'SCHEDULER': SchedulerManager})
    out = root.get_gui_options()
    # out=sched.get_gui_options(accounts=['minnie','clarabella'],queues=['prima_coda_indefinita','gll_user_prd'])
    logger.debug(" Root: " + json.dumps(out, indent=4))
    res = root.substitute(config.conf['test'])
    for k, v in res.items():
        print(k, ":::>")
        print(v)
