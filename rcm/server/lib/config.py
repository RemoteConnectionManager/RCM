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


logger = logging.getLogger('rcmServer' + '.' + __name__)


def absolute_paths(relative_paths, search_paths=(), glob_suffix=None):
    list_paths = []
    for path in relative_paths:
        abs_path = os.path.abspath(path)

        if os.path.isfile(abs_path):
            list_paths.append(abs_path)
            continue

        if os.path.isdir(abs_path):
            if glob_suffix:
                list_paths.extend(sorted(glob.glob(os.path.join(abs_path, glob_suffix))))
            else:
                list_paths.append(abs_path)
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


def getConfig(name="default", paths=(), glob_suffix="*.yaml"):
    # load and merge yaml config from config_paths by loading logging
    # being a singleton , this first call define  the yaml files that are loaded
    # subsequent calls, reuse the same info, even if change the list_paths

    if name in dict_paths:
        return dict_paths[name]

    default_paths = [os.path.join('etc', 'defaults'),
                     'etc',
                     os.path.join('etc', 'site')]

    env_config_base_path = os.environ.get("RCM_CONFIG_BASE_PATH", None)
    env_config_paths = os.environ.get("RCM_CONFIG_PATHS", '').split(':')

    search_paths = [os.path.join(root_rcm_path, 'server')]

    list_paths = list()
    list_paths.extend(absolute_paths(default_paths, search_paths))
    logger.debug("relative list paths after defaults : " + str(list_paths))
    if env_config_base_path:
        search_paths = absolute_paths([env_config_base_path], search_paths) + search_paths
    list_paths.extend(absolute_paths(env_config_paths, search_paths))
    logger.debug("relative list paths after environment: " + str(list_paths))
    list_paths.extend(paths)

    logger.debug("relative list paths: " + str(list_paths))
    list_paths = absolute_paths(list_paths, search_paths, glob_suffix)

    out = 'config: parsing: \n'
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
