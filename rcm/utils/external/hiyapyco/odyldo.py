# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent nu fileencoding=utf-8
from __future__ import unicode_literals
"""
ODYLDo - Ordered Dict Yaml Loader / Dumper
------------------------------------------

a simple implementation of a Ordered Dict Loader for PyYAML;
because chaos is fun but order matters on loading dicts from a yaml file;

(c) 2014 - 2017 Klaus Zerwes zero-sys.net
This package is free software.
This software is licensed under the terms of the
GNU GENERAL PUBLIC LICENSE version 3 or later,
as published by the Free Software Foundation.
See https://www.gnu.org/licenses/gpl.html
"""

try:
    from collections import OrderedDict
except ImportError:
    # try importing the backported replacement
    # requires a: `pip-2.6 install ordereddict`
    from ordereddict import OrderedDict 

import yaml
import yaml.loader
import yaml.dumper
import yaml.representer

# @see: yaml.resolver.DEFAULT_MAPPING_TAG
ODYLDoYAMLMAPS = [
    'tag:yaml.org,2002:map',
    'tag:yaml.org,2002:omap',
    ]

class ODYL(yaml.SafeLoader):
    """Ordered Dict Yaml Loader"""
    def __init__(self, *args, **kwargs):
        yaml.SafeLoader.__init__(self, *args, **kwargs)
        for mapping in ODYLDoYAMLMAPS:
            self.add_constructor(mapping, type(self)._odyload)

    # see pyyaml constructors construct_*
    def _odyload(self, node):
        if node.tag not in ODYLDoYAMLMAPS:
            raise Exception('called ODYLoad for unregistered mapping mode "%s" aka. "%s"' % (node.tag, node.id,))
        data = OrderedDict()
        yield data
        data.update(self.construct_mapping(node))

    # see pyyaml construct_mapping
    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)
        m = OrderedDict()
        for k, v in node.value:
            m[self.construct_object(k, deep=deep)] = self.construct_object(v, deep=deep)
        return m

class ODYD(yaml.SafeDumper):
    """Ordered Dict Yaml Dumper"""
    def __init__(self, *args, **kwargs):
        yaml.SafeDumper.__init__(self, *args, **kwargs)
        yaml.representer.SafeRepresenter.add_representer(OrderedDict, type(self)._odyrepr)
    def _odyrepr(self, data):
        """see: yaml.representer.represent_mapping"""
        return self.represent_mapping('tag:yaml.org,2002:map', data.items())

def safe_load(stream):
    """implementation of safe loader using Ordered Dict Yaml Loader"""
    return yaml.load(stream, ODYL)

def safe_dump(data, stream=None, **kwds):
    """implementation of safe dumper using Ordered Dict Yaml Dumper"""
    return yaml.dump(data, stream=None, Dumper=ODYD, **kwds)

