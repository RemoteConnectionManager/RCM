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

#singleton config class that parse cascading yaml files
class CascadeYamlConfig:
    class __CascadeYamlConfig:
        def __init__(self,listpaths=[]):
            self.conf=OrderedDict()
            if listpaths :
                self.listpaths=listpaths
            else:
                self.listpaths = glob.glob(os.path.join(os.path.dirname(os.path.realpath(__file__)), "*.yaml"))

        def parse(self):
            print("CascadeYamlConfig: parsing: ",self.listpaths)
            if(self.listpaths):
                self.conf = utils.hiyapyco.load(
            #        *[os.path.join(argfile_parser.parse_known_args()[0].config_paths,'defaults.yaml'),
            #        argfile_parser.parse_known_args()[0].args_file],
                    *self.listpaths,
                    interpolate=True,
                    method=utils.hiyapyco.METHOD_MERGE,
                    failonmissingfiles=False
                    )

        def get_copy(self,nested_key_list=[]):
            val=self.conf
            for k in nested_key_list:
                val=val.get(k,dict())
            return copy.deepcopy(val)

    instance = None
    def __init__(self, listpaths=[]):
        if not CascadeYamlConfig.instance:
            CascadeYamlConfig.instance = CascadeYamlConfig.__CascadeYamlConfig(listpaths)
            CascadeYamlConfig.instance.parse()

    def __getattr__(self, name):
        return getattr(self.instance, name)

#Base scheduler class
class BaseScheduler:

    NAME = None

    def __init__(self,schema=None):
        if schema:
            self.schema=schema
        else:
            self.schema=CascadeYamlConfig().get_copy(['defaults','SCHEDULER'])

    def get_gui_options(self,accounts=[],queues=[]):
        if not accounts:
            accounts=self.preset().get('accounts',[])

        queue_preset =self.preset().get('queues',OrderedDict())
        if not queues:
            queues=queue_preset
        print("accounts: ",accounts)
        print("queues  : ",queue_preset)
        queue_schema=copy.deepcopy(self.schema['list']['QUEUE'])
        queue_choices=OrderedDict()
        for q in queues :
            #print(q,queue_preset[q])
            l=copy.deepcopy(queue_schema['list'])
            if queue_preset.get(q,dict()) :
                for w in queue_preset.get(q,dict()):
                    print(w,queue_preset[q][w])
                    for m in queue_preset[q][w]:
                        l[w]['values'][m]=queue_preset[q][w][m]
            queue_choices[q] = {'list' : l}
        queue_schema['choices']=queue_choices
        del queue_schema['list']
        out = {'list' : copy.deepcopy(self.schema['list'])}
        out['list']['QUEUE']=queue_schema
        if(accounts) :
            out['list']['ACCOUNT']['values']=accounts

        return out


    @classmethod
    def preset(cls):
        if cls.NAME :
            return  CascadeYamlConfig().get_copy(['composites','schedulers', cls.NAME])

class SlurmScheduler(BaseScheduler):
     NAME = 'Slurm'

     def get_accounts(self):
         return ['acct1', 'acct2', 'acct3']

     def get_queues(self):
         return ['gll_user_prd', 'zqueue1', 'gll_sys_prd','aqueue2']

     def get_gui_options(self,accounts=[],queues=[]):
         return BaseScheduler.get_gui_options(self,accounts=self.get_accounts(), queues=self.get_queues())

class PBSScheduler(BaseScheduler):
    NAME = 'PBS'


if __name__ == '__main__':

    config=CascadeYamlConfig()

    sched=SlurmScheduler()

    out=sched.get_gui_options(accounts=['minnie','clarabella'],queues=['prima_coda_indefinita','gll_user_prd'])
    print("Slurm-->" + json.dumps(out, indent=4))
#scheduler composition

#scheduler=copy.deepcopy(conf['defaults']['SCHEDULER'])
scheduler=config.get_copy(['defaults','SCHEDULER'])
scheduler_choices=OrderedDict()
scheduler_list=config.get_copy(['composites','schedulers'])
for s in scheduler_list:
    if scheduler_list[s] :
        accounts=copy.deepcopy(scheduler_list[s].get('accounts',[]))
        print("accounts-->",accounts)
        #queue=copy.deepcopy(conf['defaults']['SCHEDULER']['list']['QUEUE'])
        queue=copy.deepcopy(scheduler['list']['QUEUE'])
        queue_choices=OrderedDict()
        queue_list=scheduler_list[s].get('queues',dict())
        for q in queue_list :
            print(q,queue_list[q])
            l=copy.deepcopy(queue['list'])
            if queue_list[q] :
                for w in queue_list.get(q,dict()):
                    print(w,queue_list[q][w])
                    for m in queue_list[q][w]:
                        l[w]['values'][m]=queue_list[q][w][m]
            queue_choices[q] = {'list' : l}
        queue['choices']=queue_choices
        del queue['list']

        scheduler_choices[s] = {'list' : copy.deepcopy(scheduler['list'])}
        scheduler_choices[s]['list']['QUEUE']=queue
        if(accounts) :
            scheduler_choices[s]['list']['ACCOUNT']['values']=accounts
scheduler['choices']=scheduler_choices
del scheduler['list']

print ("scheduler-->" + json.dumps(scheduler,indent=4))
