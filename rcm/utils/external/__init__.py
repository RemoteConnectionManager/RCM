from __future__ import absolute_import
import os,sys

basepath = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, basepath)
if sys.version_info.major == 3 :
    sys.path.insert(0, os.path.join(basepath,'PyYAML-3.13','lib3'))
else:
    sys.path.insert(0, os.path.join(basepath,'PyYAML-3.13','lib'))
#from . import hiyapyco,yaml



#from .linkfiles import LinkTree
#from .introspect import baseintrospect, myintrospect
#from .git_wrap import git_repo, get_branches, trasf_match

#print("###TOP in__init__ ######## "+__name__)

