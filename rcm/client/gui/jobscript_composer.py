# stdlib
import json
import sys
import os
import copy
import re
from collections import OrderedDict

root_rcm_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_rcm_path)

import utils


if __name__ == '__main__':
    import glob
    basepath = os.path.dirname(os.path.realpath(__file__))

    print("basepath:", basepath)
    print("rootpath:", root_rcm_path)

    listpaths=glob.glob(os.path.join(basepath,"*.yaml"))
    if(listpaths):
        conf = utils.hiyapyco.load(
    #        *[os.path.join(argfile_parser.parse_known_args()[0].config_paths,'defaults.yaml'),
    #        argfile_parser.parse_known_args()[0].args_file],
            *listpaths,
            interpolate=True,
            method=utils.hiyapyco.METHOD_MERGE,
            failonmissingfiles=False
            )

#scheduler composition

scheduler=copy.deepcopy(conf['defaults']['SCHEDULER'])
scheduler_choices=OrderedDict()
scheduler_list=conf['composites']['schedulers']
for s in scheduler_list:
    if scheduler_list[s] :
        accounts=copy.deepcopy(scheduler_list[s].get('accounts',dict()))
        queue=copy.deepcopy(conf['defaults']['SCHEDULER']['list']['QUEUE'])
        del queue['list']
        queue_choices=OrderedDict()
        queue_list=scheduler_list[s].get('queues',dict())
        for q in queue_list :
            print(q,queue_list[q])
            l=copy.deepcopy(conf['defaults']['SCHEDULER']['list']['QUEUE']['list'])
            if queue_list[q] :
                for w in queue_list.get(q,dict()):
                    print(w,queue_list[q][w])
                    for m in queue_list[q][w]:
                        l[w]['values'][m]=queue_list[q][w][m]
            queue_choices[q] = {'list' : l}
        queue['choices']=queue_choices

        scheduler_choices[s] = {'list' : copy.deepcopy(conf['defaults']['SCHEDULER']['list'])}
        scheduler_choices[s]['list']['QUEUE']=queue
        if(accounts) :
            scheduler_choices[s]['list']['ACCOUNT']['values']=accounts
scheduler['choices']=scheduler_choices
del scheduler['list']

print ("scheduler-->" + json.dumps(scheduler,indent=4))
for k in conf.keys():
    root_val=conf[k]
    for d in root_val:
        print(k + " :"+ d + ' --> ' + json.dumps(root_val[d]))
