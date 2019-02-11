# stdlib

import logging
import json
import copy
from collections import OrderedDict

#root_rcm_path = os.path.dirname((os.path.dirname(os.path.abspath(__file__))))
#sys.path.append(root_rcm_path)

#import utils
from utils.cascade_yaml_config import *

logger = logging.getLogger('RCM.composer')


class BaseGuiComposer(object):
    NAME = None
    working = True

    def __init__(self, schema=None, name=None, defaults=None, class_table=None):

        print(self.__class__.__name__, name)
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


    def substitute(self, choices):
        t = ""
        if self.templates:
            t = " -subst- "+str(self.templates)
        logger.debug(" " + self.__class__.__name__ + " : " + str(self.NAME) + " : " + t + str(choices))


class LeafGuiComposer(BaseGuiComposer):

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


class CompositeComposer(BaseGuiComposer):

    def __init__(self, *args, **kwargs):
        super(CompositeComposer, self).__init__(*args, **kwargs)
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def get_gui_options(self):
        options = OrderedDict()
        for child in self.children:
            options[child.NAME] = child.get_gui_options()
        return options

    def substitute(self, choices):
        BaseGuiComposer.substitute(self, choices)
        for child in self.children:
            child.substitute(choices)


class ChoiceGuiComposer(CompositeComposer):

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


class AutoChoiceGuiComposer(CompositeComposer):

    def __init__(self, *args, **kwargs):
        super(AutoChoiceGuiComposer, self).__init__(*args, **kwargs)

        for child_name in self.schema:
            print("#########",child_name)
            child_schema = copy.deepcopy(self.schema[child_name])
            if child_name in self.defaults:
                if 'list' in child_schema:
                    manager_class = self.class_table.get(child_name, AutoManagerChoiceGuiComposer)
                    child = manager_class(name=child_name,
                                          schema=copy.deepcopy(child_schema),
                                          defaults=copy.deepcopy(self.defaults[child_name]))
                else:
                    logger.debug("hadling leaf item: " + child_name)
                    child = LeafGuiComposer(name=child_name,
                                            schema=copy.deepcopy(child_schema),
                                            defaults=copy.deepcopy(self.defaults[child_name]))
                self.add_child(child)
            else:
                if 'list' in child_schema:
                    logger.debug("skipping complex item: " + child_name + "in schema but not in defaults")
                else:
                    logger.debug("adding leaf item: " + child_name + "without defaults")
                    child = LeafGuiComposer(name=child_name,
                                            schema=copy.deepcopy(child_schema),
                                            defaults=OrderedDict())
                    self.add_child(child)

    def substitute(self, choices):
        # in_subst is the dict of susbstitutions that are passed to child nodes
        # these substs are initialized with self.templates ( current node defined susbstitutions)
        # to provide defaults that are overridden by choices
        in_subst=copy.deepcopy(self.templates)
        in_subst.update(copy.deepcopy(choices))

        BaseGuiComposer.substitute(self, choices)
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
        out_subst=OrderedDict()
        for child in self.children:
            if child_subst[child]:
                # logger.debug(child_subst[child])
                subst = child.substitute(child_subst[child])
                print("child:",child.NAME," returned ",subst)
                if subst:
                    for key_sub in subst:
                        in_subst[key_sub] = subst[key_sub]
                        # substitutions coming from child are reported upstream by prepending
                        # self.schema_name, the current node schema name
                        out_subst[self.schema_name + '.' + key_sub] = subst[key_sub]
        print("in", self.NAME, self.schema_name,  "substitute:",in_subst,"\ninto",self.templates)
        #out_subst = copy.deepcopy(self.templates)
        out_subst.update(copy.deepcopy(self.templates))
        for t in self.templates:
            out_subst[t] = utils.stringtemplate(self.templates[t]).safe_substitute(in_subst)

        for key, value in out_subst.items():
            logger.debug(" AutoChoiceGuiComposer: " + str(self.NAME) + " : " + str(key) + " ::> " + str(value))

        return out_subst


class ManagedChoiceGuiComposer(AutoChoiceGuiComposer):

    def get_gui_options(self):
        options = OrderedDict()
        for child in self.children:
            options[child.NAME] = child.get_gui_options()
        return {'list': options}


class ManagerChoiceGuiComposer(ChoiceGuiComposer):

    def substitute(self, choices):
        BaseGuiComposer.substitute(self, choices)
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
                return child.substitute(child_subst[child])


class AutoManagerChoiceGuiComposer(ManagerChoiceGuiComposer):

    def __init__(self, *args, **kwargs):
        super(AutoManagerChoiceGuiComposer, self).__init__(*args, **kwargs)
        if 'list' in self.schema:
            for class_name in self.defaults:
                logger.debug("handling child  : " + class_name)
                child = ManagedChoiceGuiComposer(name=class_name,
                                                 schema=copy.deepcopy(self.schema['list']),
                                                 defaults=copy.deepcopy(self.defaults.get(class_name, OrderedDict())))
                # here we override child shema_name, as is neede to be different from instance class name
                # WARNING.... external set of member variable outside object methods
                child.schema_name=self.NAME
                self.add_child(child)


