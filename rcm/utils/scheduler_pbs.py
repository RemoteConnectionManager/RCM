# stdlib
import sys
import os
import logging
import json
import copy

from collections import OrderedDict

root_rcm_path = os.path.dirname((os.path.dirname(os.path.abspath(__file__))))
if root_rcm_path not in sys.path:
    sys.path.append(root_rcm_path)



from utils.jobscript_composer_base import *
from utils.scheduler_base import *
from utils.scheduler_slurm import *
#from utils import  jobscript_composer_base
#from utils import  scheduler_base

logger = logging.getLogger('RCM.composer')


class PBSScheduler(BatchScheduler):
    NAME = 'PBS'
    # commands = {'qstat': None}


class LocalScheduler(BaseScheduler):
    NAME = 'Local'


class SSHScheduler(BaseScheduler):
    NAME = 'SSH'


if __name__ == '__main__':

    root_rcm_path = os.path.dirname((os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(root_rcm_path)

    #This is needed, otherwise no default logging happen
    logging.debug("Start test app")
    logger = logging.getLogger('RCM.composer')
    logger.setLevel(logging.INFO)

    list_paths = []
    #list_paths.append(os.path.join(os.environ.get('HOME',''), '.rcm', 'config', 'config.yaml'))
    list_paths.append('test')
    config = CascadeYamlConfig(list_paths = list_paths)
    SchedulerManager.register_scheduler([SlurmScheduler, PBSScheduler, LocalScheduler])
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
