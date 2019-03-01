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


class CascadeYamlConfig:
    """
    singleton ( pattern from https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html )
    config class that parse cascading yaml files with hiyapyco
    constructor take a list of files that are parsed hierachically by parse method
    """

    class __CascadeYamlConfig:
        def __init__(self, list_paths=None, use_default_paths=True, use_environment=True, glob_suffix="*.yaml"):
            self._conf = OrderedDict()
            self.list_paths = []
            default_paths=[]
            for path in ['etc', os.path.join('etc', 'defaults')]:
                default_paths.append(os.path.join(root_rcm_path, 'server', path))
            search_paths = []
            if list_paths:
                input_list_paths = list_paths
            else:
                input_list_paths = []
            if use_environment:
                use_default_paths = os.environ.get("RCM_CONFIG_USE_DEFAULTS", use_default_paths)
                env_config_base_path = os.environ.get("RCM_CONFIG_BASE_PATH", None)
                if env_config_base_path:
                    for path in [env_config_base_path,
                                 os.path.join(root_rcm_path, 'server', env_config_base_path)]:
                        if os.path.isdir(path) and os.path.exists(path):
                            env_config_base_path = path
                            break
                        else:
                            env_config_base_path = None

                env_config_paths = os.environ.get("RCM_CONFIG_PATHS", None)
                if env_config_paths:
                    for path in env_config_paths.split(":"):
                        input_list_paths.append(path)

            print("@@@@@@@@@@@@@",input_list_paths)
            if input_list_paths:
                logger.info("CascadeYamlConfig: list_paths: " + str(list_paths))

                if use_environment and env_config_base_path:
                    search_paths.append(env_config_base_path)
                if use_default_paths:
                   search_paths.append(default_paths[0])
                print("@@@@@@@@@@@@@ search_paths", search_paths)
                for path in input_list_paths:
                    if os.path.isfile(path) and os.path.exists(path):
                        self.list_paths.append(path)
                    else:
                        if os.path.isdir(path) and os.path.exists(path):
                            self.list_paths.extend(glob.glob(os.path.join(path, glob_suffix)))
                        else:
                            # path not exist, searching it as relative path
                            found_path=None
                            for base_path in search_paths:
                                abs_path = os.path.join(base_path, path)
                                if os.path.exists(abs_path):
                                    found_path = abs_path
                                    break
                            if found_path:
                                self.list_paths.extend(glob.glob(os.path.join(found_path, glob_suffix)))
                            else:
                                logger.warning('use_default_path: ' + abs_path + ' not found')
            else:
                use_default_paths = True
            if use_default_paths:
                for path in default_paths:
                    self.list_paths.extend(glob.glob(os.path.join(path, glob_suffix)))

            self.list_paths.reverse()

        def parse(self):
            logger.info("CascadeYamlConfig: parsing: " + str(self.list_paths))
            print("CascadeYamlConfig: parsing: " + str(self.list_paths))
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


