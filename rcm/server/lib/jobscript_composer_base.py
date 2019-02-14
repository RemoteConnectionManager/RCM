# stdlib

import logging
import json
import copy
from collections import OrderedDict

#root_rcm_path = os.path.dirname((os.path.dirname(os.path.abspath(__file__))))
#sys.path.append(root_rcm_path)

#import utils
from cascade_yaml_config import *

logger = logging.getLogger('RCM.composer')


class Node(object):
    NAME = None
    working = True

    def __init__(self, schema=None, name=None, defaults=None, class_table=None):

        #shut#print(self.__class__.__name__, name)
        if name:
            self.NAME = name
        if self.NAME:
            self.schema_name=self.NAME
        else:
            self.schema_name='UNKNOWN'
        if schema:
            self.schema = schema
        else:
            # self.schema = CascadeYamlConfig().get_copy(['schema', self.NAME])
            self.schema = CascadeYamlConfig()['schema', self.NAME]
        if defaults:
            self.defaults = defaults
        else:
            self.defaults = CascadeYamlConfig()['defaults', self.NAME]
        if class_table:
            self.class_table = class_table
        else:
            self.class_table = dict()
        logger.debug(self.__class__.__name__ + ": " + str(self.NAME))
        logger.debug("self.schema " + str(self.schema))
        logger.debug("self.defaults " + str(self.defaults))

        self.templates = copy.deepcopy(self.schema.get('substitutions', OrderedDict()))
        # needed to prevent crash when key susbstitutions has no following substitutions
        if self.templates is None:
            self.templates = OrderedDict()
        if hasattr(self.defaults, 'get'):
            default_subst = copy.deepcopy(self.defaults.get('substitutions', OrderedDict()))
            # needed to prevent crash when key susbstitutions has no following substitutions
            if hasattr(default_subst, '__getitem__'):
                for key in default_subst:
                    self.templates[key] = default_subst[key]
        logger.debug(" template: " + self.__class__.__name__ + ": " + str(self.NAME) + " " + str(self.templates))
        for d in [self.schema, self.defaults]:
            if 'substitutions' in d:
                del d['substitutions']

        print("init of ",self.__class__.__name__,self.NAME)

    def substitute(self, choices):
        t = ""
        if self.templates:
            t = " -subst- "+str(self.templates)
        logger.debug(" " + self.__class__.__name__ + " : " + str(self.NAME) + " : " + t + str(choices))


class LeafNode(Node):

    def get_gui_options(self):
        options = copy.deepcopy(self.schema)
        if 'values' in options:
            for preset in self.defaults:
                options['values'][preset] = self.defaults[preset]
        else:
            options['values'] = copy.deepcopy(self.defaults)
        return options

    def substitute(self, choices):
        out_subst = choices
        for t in self.templates:
            out_subst[t] = utils.stringtemplate(self.templates[t]).safe_substitute(choices)

        for key, value in out_subst.items():
            logger.debug(" leaf: " + str(self.NAME) + " : " + str(key) + " ::> " + str(value))
        return out_subst


class CompositeNode(Node):

    def __init__(self, *args, **kwargs):
        super(CompositeNode, self).__init__(*args, **kwargs)
        self.children = []
        self.active_child=None

    def add_child(self, child):
        self.children.append(child)

    def get_gui_options(self):
        options = OrderedDict()
        for child in self.children:
            options[child.NAME] = child.get_gui_options()
        return options

    def substitute(self, choices):
        print("@@@@@@@@@@@@@@  HERE")
        Node.substitute(self, choices)
        for child in self.children:
            child.substitute(choices)


class ChoiceNode(CompositeNode):

    def get_gui_options(self):
        composer_options = self.schema
        composer_choice = OrderedDict()
        if self.children:
            for child in self.children:
                composer_choice[child.NAME] = child.get_gui_options()
            composer_options['choices'] = composer_choice
        if 'list' in composer_options:
            del composer_options['list']
        return composer_options


class AutoChoiceNode(CompositeNode):

    def __init__(self, *args, **kwargs):
        super(AutoChoiceNode, self).__init__(*args, **kwargs)

        for child_name in self.schema:
            #shut#print("#########",child_name)
            child_schema = copy.deepcopy(self.schema[child_name])
            if child_name in self.defaults:
                if 'list' in child_schema:
                    manager_class = self.class_table.get(child_name, AutoManagerChoiceNode)
                    child = manager_class(name=child_name,
                                          schema=copy.deepcopy(child_schema),
                                          defaults=copy.deepcopy(self.defaults[child_name]))
                else:
                    logger.debug("hadling leaf item: " + child_name)
                    child = LeafNode(name=child_name,
                                            schema=copy.deepcopy(child_schema),
                                            defaults=copy.deepcopy(self.defaults[child_name]))
                self.add_child(child)
            else:
                if 'list' in child_schema:
                    logger.debug("skipping complex item: " + child_name + "in schema but not in defaults")
                else:
                    logger.debug("adding leaf item: " + child_name + "without defaults")
                    child = LeafNode(name=child_name,
                                            schema=copy.deepcopy(child_schema),
                                            defaults=OrderedDict())
                    self.add_child(child)

    def substitute(self, choices):
        # in_subst is the dict of susbstitutions that are passed to child nodes
        # these substs are initialized with self.templates ( current node defined susbstitutions)
        # to provide defaults that are overridden by choices

        Node.substitute(self, choices)
        child_subst = dict()
        for child in self.children:
            child_subst[child] = dict()
        for key, value in choices.items():
            # logger.debug("--in: ", self.NAME, "substitute ", key + " : " + value)
            subkey = key.split('.')
            # logger.debug(subkey)
            for child in self.children:
                if child.NAME == subkey[0]:
                    # logger.debug("stripping subst", self.NAME, "--", '.'.join(subkey[1:]) )
                    child_subst[child][key] = value

        collected_subst=OrderedDict()
        in_subst=copy.deepcopy(self.templates)
        in_subst.update(copy.deepcopy(choices))

        for child in self.children:
            if child_subst[child]:
                # logger.debug(child_subst[child])
                subst = child.substitute(child_subst[child])
                #shut#print("child:",child.NAME," returned ",subst)
                if subst:
                    for key_sub in subst:
                        in_subst[key_sub] = subst[key_sub]
                        in_subst[child.schema_name + '.' + key_sub] = subst[key_sub]
                        # substitutions coming from child are reported upstream by prepending
                        # self.schema_name, the current node schema name
                        #out_subst[self.schema_name + '.' + key_sub] = subst[key_sub]
                        if not key_sub in child_subst[child]:
                            collected_subst[child.schema_name + '.' + key_sub] = subst[key_sub]
        #shut#print("in", self.NAME, self.schema_name,  "substitute:",in_subst,"\ninto",self.templates)
        #bad#out_subst = copy.deepcopy(self.templates)
        #bad#out_subst.update(child_subst)
        #bad#for t in out_subst:
        #bad#    out_subst[t] = utils.stringtemplate(out_subst[t]).safe_substitute(in_subst)

        out_subst=OrderedDict()
        for t in self.templates:
            out_subst[t] = utils.stringtemplate(self.templates[t]).safe_substitute(in_subst)
        out_subst.update(copy.deepcopy(choices))
        out_subst.update(copy.deepcopy(collected_subst))

        for key, value in out_subst.items():
            logger.debug(" AutoChoiceNode: " + str(self.NAME) + " : " + str(key) + " ::> " + str(value))

        return out_subst


class ManagedChoiceNode(AutoChoiceNode):

    def get_gui_options(self):
        options = OrderedDict()
        for child in self.children:
            options[child.NAME] = child.get_gui_options()
        return {'list': options}


class ManagerChoiceNode(ChoiceNode):

    def substitute(self, choices):
        Node.substitute(self, choices)
        child_subst = dict()
        active_child_name = choices.get(self.NAME, '')
        for child in self.children:
            child_subst[child] = dict()
        for key, value in choices.items():
            # logger.debug("--in: ", self.NAME, "substitute ", key + " : " + value)
            subkey = key.split('.')
            # logger.debug(subkey)
            if len(subkey) > 1:
                if self.NAME == subkey[0]:
                    for child in self.children:
                        if child.NAME == active_child_name:
                            # logger.debug("stripping subst", self.NAME, "--", '.'.join(subkey[1:]) )
                            child_subst[child]['.'.join(subkey[1:])] = value
        for child in self.children:
            if child.NAME == active_child_name:
                self.active_child=child
                return child.substitute(child_subst[child])


class AutoManagerChoiceNode(ManagerChoiceNode):

    def __init__(self, *args, **kwargs):
        super(AutoManagerChoiceNode, self).__init__(*args, **kwargs)
        if 'list' in self.schema:
            for class_name in self.defaults:
                logger.debug("handling child  : " + class_name)
                child = ManagedChoiceNode(name=class_name,
                                                 schema=copy.deepcopy(self.schema['list']),
                                                 defaults=copy.deepcopy(self.defaults.get(class_name, OrderedDict())))
                # here we override child shema_name, as is neede to be different from instance class name
                # WARNING.... external set of member variable outside object methods
                child.schema_name=self.NAME
                self.add_child(child)


