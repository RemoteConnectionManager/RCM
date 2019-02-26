# stdlib
import sys
import os
import logging
import copy
import glob
from collections import OrderedDict

root_rcm_path = os.path.dirname((os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if root_rcm_path not in sys.path:
    sys.path.append(root_rcm_path)

import utils


logger = logging.getLogger('RCM.composer')

def absolute_paths(relative_paths, search_paths=(), glob_suffix=None):
    list_paths=[]
    for path in relative_paths:
        abs_path = os.path.abspath(path)

        if os.path.isfile(abs_path):
            list_paths.append(abs_path)
            continue

        if os.path.isdir(abs_path):
            if glob_suffix:
                list_paths.extend(glob.glob(os.path.join(abs_path, glob_suffix)))
            else:
                list_paths.apend(abs_path)
            continue

        # path not exist, searching it as relative path
        found_path = None
        for base_path in search_paths:
            abs_path = os.path.abspath(os.path.join(base_path, path))
            if os.path.exists(abs_path):
                found_path = abs_path
                break
        if found_path:
            if os.path.isfile(found_path):
                list_paths.append(found_path)
            else:
                if os.path.isdir(found_path):
                    if glob_suffix:
                        list_paths.extend(glob.glob(os.path.join(found_path, glob_suffix)))
                    else:
                        list_paths.append(found_path)
        else:
            logger.warning('path: ' + path + ' not found in ' + str(search_paths))

    return list_paths


class MyOrderedDict:
    def __init__(self, configuration):
        self.configuration = configuration

    def __getitem__(self, key_list):
        val = self.configuration
        if key_list:
            if isinstance(key_list, tuple):
                for key in key_list:
                    val = val.get(key, OrderedDict())
                    if not val:
                        val = OrderedDict()
            else:
                val = val.get(key_list, OrderedDict())
            return copy.deepcopy(val)


dict_paths = dict()


def getConfig(name="default", paths=(),  use_default_paths=True, glob_suffix="*.yaml"):
    # load and merge yaml config from config_paths by loading logging
    # being a singleton , this first call define  the yaml files that are loaded
    # subsequent calls, reuse the same info, even if change the list_paths

    if name in dict_paths:
        return dict_paths[name]

    default_paths = [os.path.join('etc', 'defaults'), 'etc']

    use_default_paths = os.environ.get("RCM_CONFIG_USE_DEFAULTS", use_default_paths)
    env_config_base_path = os.environ.get("RCM_CONFIG_BASE_PATH", None)
    env_config_paths = os.environ.get("RCM_CONFIG_PATHS", '').split(':')

    search_paths = [os.path.join(root_rcm_path, 'server')]

    list_paths = list()
    list_paths.extend(absolute_paths(default_paths, search_paths))
    print("relative list paths after defaults : " + str(list_paths))
    if env_config_base_path:
        search_paths = absolute_paths([env_config_base_path], search_paths) + search_paths
    list_paths.extend(absolute_paths(env_config_paths, search_paths))
    print("relative list paths after environment: " + str(list_paths))
    list_paths.extend(paths)

    print("relative list paths: " + str(list_paths))
    list_paths = absolute_paths(list_paths, search_paths, glob_suffix)

    out='config: parsing: \n'
    for path in list_paths:
        out += '  ' + path + '\n'
    logger.info(out)


    conf = utils.hiyapyco.load(
        *list_paths,
        interpolate=True,
        method=utils.hiyapyco.METHOD_MERGE,
        failonmissingfiles=False
    )

    dict_paths[name] = MyOrderedDict(conf)
    return copy.deepcopy(dict_paths[name])



class CascadeYamlConfig:
    """
    singleton ( pattern from https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html )
    config class that parse cascading yaml files with hiyapyco
    constructor take a list of files that are parsed hierachically by parse method
    """

    class __CascadeYamlConfig:
        def __init__(self, list_paths=None, use_default_paths=True, glob_suffix="*.yaml"):
            self._conf = OrderedDict()
            self.list_paths = []
            if list_paths:
                input_list_paths = list_paths
            else:
                input_list_paths = []
            if use_default_paths:
                env_config_path = os.environ.get("RCM_CONFIG_PATH", None)
                if env_config_path:
                    input_list_paths.append(env_config_path)
            if list_paths:
                logger.info("CascadeYamlConfig: list_paths: " + str(list_paths))
                for path in list_paths:
                    if os.path.isfile(path) and os.path.exists(path):
                        self.list_paths.append(path)
                    else:
                        if os.path.isdir(path) and os.path.exists(path):
                            self.list_paths.extend(glob.glob(os.path.join(path, glob_suffix)))
                        else:
                            if use_default_paths:
                                abs_path = os.path.join(root_rcm_path,
                                                        'server',
                                                        'etc',
                                                        path)
                                if os.path.exists(abs_path):
                                    self.list_paths.extend(glob.glob(os.path.join(abs_path, glob_suffix)))
                                else:
                                    logger.warning('use_default_path: ' + abs_path + ' not found')
            else:
                use_default_paths = True
            if use_default_paths:
                for path in ['etc', os.path.join('etc', 'defaults')]:
                    self.list_paths.extend(glob.glob(os.path.join(root_rcm_path,
                                                                  'server',
                                                                  path,
                                                                  glob_suffix)))

            self.list_paths.reverse()

        def parse(self):
            logger.info("CascadeYamlConfig: parsing: " + str(self.list_paths))
            if self.list_paths:
                self._conf = utils.hiyapyco.load(
                    *self.list_paths,
                    interpolate=True,
                    method=utils.hiyapyco.METHOD_MERGE,
                    failonmissingfiles=False
                )

        @property
        def conf(self):
            return copy.deepcopy(self._conf)

        def __getitem__(self, nested_key_list=None):
            """
            this funchion access parsed config as loaded from hiyapyco
            :param nested_key_list: list of the nested keys to retrieve
            :return: deep copy of OrderedDict
            """
            val = self._conf
            if nested_key_list:
                for key in nested_key_list:
                    val = val.get(key, OrderedDict())
# this is needed to avoid crash on accessing empty keys
                    if not val:
                        val = OrderedDict()
            return copy.deepcopy(val)

    instance = None

    def __init__(self, list_paths=None, use_default_paths=True, glob_suffix="*.yaml"):
        if not CascadeYamlConfig.instance:
            CascadeYamlConfig.instance = CascadeYamlConfig.__CascadeYamlConfig(list_paths=list_paths, use_default_paths=use_default_paths, glob_suffix=glob_suffix)
            CascadeYamlConfig.instance.parse()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __getitem__(self, nested_key_list):
        return self.instance.__getitem__(nested_key_list)

