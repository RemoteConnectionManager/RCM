# std import
import logging
import json
import copy
from collections import OrderedDict

# local import
#from config import *
import config
import utils

logger = logging.getLogger('rcmServer')
module_logger = logging.getLogger('rcmServer' + '.' + __name__)
constructor_logger = logging.getLogger('rcmServer' + '.' + __name__ + '.' + 'constructor')
gui_logger = logging.getLogger('rcmServer' + '.' + __name__ + '.' + 'gui')
substitute_logger = logging.getLogger('rcmServer' + '.' + __name__ + '.' + 'substitute')

try:  # check whether python knows about 'basestring'
    stringtypes = (str, unicode)
except NameError:  # no, it doesn't (it's Python3); use 'str' instead
    stringtypes = (str,)

class_table=None

class Node(object):
    """
    Base class for tree nodes representing jobscript composotion and gui widget hierarchy.
    It instantiate a tree of nodes derived from this one, taking OrderedDict data loaded in yaml
    format from CascadeYamlConfig or passed trough __init__ constructor params.
    it also accept it' s name as input (the name can be specilizes such as Slurm, name of the queue or generic such as QUEUE or SCHEDULER
    it keep also a schema name that if not redefined is equal to name, schema name can be redefines

    """
    NAME = None

    def __init__(self, schema=None, name=None, defaults=None, connected_plugin=None):

        if name:
            self.NAME = name
        if self.NAME:
            self.schema_name=self.NAME
        else:
            self.schema_name='UNKNOWN'
        if schema:
            constructor_logger.debug(self.__class__.__name__ + " " +  self.NAME + " getting input schema " + str(schema))
            self.schema = schema
        else:
            self.schema = config.getConfig()['schema', self.NAME]
            constructor_logger.debug(self.__class__.__name__ +  " " +  self.NAME + " getting yaml schema " + str(self.schema) )

        if defaults:
            constructor_logger.debug(self.__class__.__name__ + " " +  self.NAME + " getting input defaults " + str(defaults))
            self.defaults = defaults
        else:
            self.defaults = config.getConfig()['defaults', self.NAME]
            constructor_logger.debug(self.__class__.__name__ + " " +  self.NAME + " getting yaml defaults " + str(self.defaults))
        self.connected_plugin = connected_plugin
        module_logger.debug(self.__class__.__name__ + ": " + str(self.NAME))

        self.templates = copy.deepcopy(self.schema.get('substitutions', OrderedDict()))
        constructor_logger.debug(self.__class__.__name__ + " " +  self.NAME + " templates schema  " + str(self.templates))
        # needed to prevent crash when key susbstitutions has no following substitutions
        if self.templates is None:
            self.templates = OrderedDict()
        if hasattr(self.defaults, 'get'):
            default_subst = copy.deepcopy(self.defaults.get('substitutions', OrderedDict()))
            constructor_logger.debug(self.__class__.__name__ + " " +  self.NAME + " templates defaults " + str(default_subst))
        # needed to prevent crash when key susbstitutions has no following substitutions
            # needed to prevent crash when key susbstitutions has no following substitutions
            if hasattr(default_subst, '__getitem__'):
                for key in default_subst:
                    self.templates[key] = default_subst[key]

                # for key,val  in default_subst.items():
                #     if type(val) in stringtypes:
                #         self.templates[key] = str(default_subst[key])
                #     else:
                #         if type(val) is list:
                #             outlist=[]
                #             for v  in val:
                #                 if type(v) in stringtypes:
                #                     print("############# " + key + " ####>"+str(v)+"<###")
                #                     outlist.append(str(v))
                #                 else:
                #                     outlist.append(v)
                #                     substitute_logger.warning(
                #                         " " + self.__class__.__name__ + " : " + str(
                #                         self.NAME) + "key: " + key + " unknown type value " + str(
                #                         type(v)) + " : " + str(v))
                #
                #             self.templates[key] = outlist
                #         else:
                #             self.templates[key] = default_subst[key]
                #     print("@+@+@ " + key + "-->" + str(default_subst[key]) + "<--")

        constructor_logger.debug(self.__class__.__name__ + " " +  self.NAME + " templates merged " + str(self.templates))


    def substitute(self, choices):
        t = ""
        if self.templates:
            t = " -subst- "+str(self.templates)
        substitute_logger.debug(" " + self.__class__.__name__ + " : " + str(self.NAME) + " : " + t + str(choices))


class LeafNode(Node):

    def get_gui_options(self):
        options = copy.deepcopy(self.schema)
        if 'values' in options:
            for preset in self.defaults:
                options['values'][preset] = self.defaults[preset]
        else:
            options['values'] = copy.deepcopy(self.defaults)
        gui_logger.debug(self.__class__.__name__ + " gui options " + str(options))
        return options

    def substitute(self, choices):
        out_subst = choices
        for t in self.templates:
            out_subst[t] = utils.StringTemplate(self.templates[t]).safe_substitute(choices)

        for key, value in out_subst.items():
            substitute_logger.debug(" " + self.__class__.__name__ + " : " + str(self.NAME) + " : " + " leaf: " + str(self.NAME) + " : " + str(key) + " ::> " + str(value))
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
#        for keyword in ['children', 'substitutions']:
#            if keyword in options:
#                del options[keyword]

        gui_logger.debug(self.__class__.__name__ + " gui options " + str(options))
        return options

    def substitute(self, choices):
        gui_logger.debug("@@@@@@@@@@@@@@  HERE")
        Node.substitute(self, choices)
        for child in self.children:
            child.substitute(choices)


class ChoiceNode(CompositeNode):

    def get_gui_options(self):
        composer_options=OrderedDict()
        excluded_keys = ['children', 'substitutions']
        for keyword in self.schema:
            if not keyword in excluded_keys:
                composer_options[keyword] = self.schema[keyword]
        composer_choice = OrderedDict()
        if self.children:
            for child in self.children:
                composer_choice[child.NAME] = child.get_gui_options()
            composer_options['values'] = composer_choice
        return composer_options


class AutoChoiceNode(CompositeNode):

    def __init__(self, *args, **kwargs):
        super(AutoChoiceNode, self).__init__(*args, **kwargs)

        children_schema =  self.schema.get('children', OrderedDict())
        if children_schema:
            for child_name in children_schema:
                child_schema = copy.deepcopy(children_schema[child_name])
                if child_name in self.defaults:
                    if 'children' in child_schema:
                        #(manager_class, plugin_instances) = self.class_table.get(child_name, (AutoManagerChoiceNode,None))
                        child = AutoManagerChoiceNode(name=child_name,
                                              schema=copy.deepcopy(child_schema),
                                              defaults=copy.deepcopy(self.defaults[child_name]))
                    else:
                        constructor_logger.debug(self.__class__.__name__ + " " +  self.NAME + " hadling leaf item: " + child_name)
                        child = LeafNode(name=child_name,
                                         schema=copy.deepcopy(child_schema),
                                         defaults=copy.deepcopy(self.defaults[child_name]))
                    self.add_child(child)
                else:
                    if child_schema:
                        if 'children' in child_schema:
                            constructor_logger.debug("skipping complex item: " + child_name + " in schema but not in defaults")
                        else:
                            if child_schema.get('values', OrderedDict()):
                                constructor_logger.debug(self.__class__.__name__ + " " +  self.NAME + " adding leaf item: " + child_name + " without defaults")
                                child = LeafNode(name=child_name,
                                             schema=copy.deepcopy(child_schema),
                                             defaults=OrderedDict())
                                self.add_child(child)
                            else:
                                constructor_logger.warning(self.__class__.__name__ + " " +  self.NAME + " skipping leaf item: " + child_name + " without defaults and no values")


    def substitute(self, choices):
        # in_subst is the dict of susbstitutions that are passed to child nodes
        # these substs are initialized with self.templates ( current node defined susbstitutions)
        # to provide defaults that are overridden by choices

        Node.substitute(self, choices)
        child_subst = dict()
        for child in self.children:
            child_subst[child] = dict()
        for key, value in choices.items():
            substitute_logger.debug(" " + self.__class__.__name__ + " : " + str(self.NAME) +  " substitute " + key + " : " + value)
            subkey = key.split('.')
            substitute_logger.debug(subkey)
            for child in self.children:
                if child.NAME == subkey[0]:
                    substitute_logger.debug("stripping subst " + str(self.NAME) +  "--" + '.'.join(subkey[1:]) )
                    child_subst[child][key] = value

        collected_subst=OrderedDict()
        in_subst=copy.deepcopy(self.templates)
        in_subst.update(copy.deepcopy(choices))

        for child in self.children:
            if child_subst[child]:
                # substitute_logger.debug(child_subst[child])
                subst = child.substitute(child_subst[child])
                substitute_logger.debug("child: " + child.NAME + " returned " + str(subst))
                if subst:
                    for key_sub in subst:
                        in_subst[key_sub] = subst[key_sub]
                        in_subst[child.schema_name + '.' + key_sub] = subst[key_sub]
                        # substitutions coming from child are reported upstream by prepending
                        # self.schema_name, the current node schema name
                        #out_subst[self.schema_name + '.' + key_sub] = subst[key_sub]
                        if not key_sub in child_subst[child]:
                            collected_subst[child.schema_name + '.' + key_sub] = subst[key_sub]

        out_subst=OrderedDict()
        for t,val in self.templates.items():
            if type(val) in stringtypes:
                out_subst[t] = utils.StringTemplate(val).safe_substitute(in_subst)
            else:
                if type(val) is list:
                    out=list()
                    for v in val:
                        if type(v) in stringtypes:
                            out.append(utils.StringTemplate(v).safe_substitute(in_subst))
                        else:
                            substitute_logger.warning(
                                " " + self.__class__.__name__ + " : " + str(
                                    self.NAME) + "key: " + t + " unknown type value " + str(type(v)) + " : " + str(v))
                    out_subst[t] = out
                else:
                    substitute_logger.warning(
                        " " + self.__class__.__name__ + " : " + str(self.NAME) + "key: " + t +" unknown type value " + str(type(val)) + " : " + val)
        out_subst.update(copy.deepcopy(choices))
        out_subst.update(copy.deepcopy(collected_subst))

        for key, value in out_subst.items():
            substitute_logger.debug(" " + self.__class__.__name__ + " : " + str(self.NAME) + " : " + str(key) + " ::> " + str(value))

        return out_subst


class ManagedChoiceNode(AutoChoiceNode):

    def get_gui_options(self):
        options = OrderedDict()
        for child in self.children:
            options[child.NAME] = child.get_gui_options()

#        for keyword in ['children', 'substitutions']:
#            if keyword in options:
#                del options[keyword]

        if options:
            return {'children': options}
        else:
            return options


class ManagerChoiceNode(ChoiceNode):

    def substitute(self, choices):
        Node.substitute(self, choices)
        child_subst = dict()
        active_child_name = choices.get(self.NAME, '')
        for child in self.children:
            child_subst[child] = dict()
        for key, value in choices.items():
            substitute_logger.debug(" " + self.__class__.__name__ + " : " + str(self.NAME) + " substitute " + key + " : " + value)
            subkey = key.split('.')
            # logger.debug(subkey)
            if len(subkey) > 1:
                if self.NAME == subkey[0]:
                    for child in self.children:
                        if child.NAME == active_child_name:
                            substitute_logger.debug(" " + self.__class__.__name__ + " : " + str(self.NAME) + " stripping subst" + self.NAME + "--" + '.'.join(subkey[1:]) )
                            child_subst[child]['.'.join(subkey[1:])] = value
        for child in self.children:
            if child.NAME == active_child_name:
                self.active_child=child
                return child.substitute(child_subst[child])


class AutoManagerChoiceNode(ManagerChoiceNode):

    def __init__(self, *args, **kwargs):
        super(AutoManagerChoiceNode, self).__init__(*args, **kwargs)
        if 'children' in self.schema and hasattr(self.defaults, 'get'):
            for class_name in self.defaults:
                constructor_logger.debug(self.__class__.__name__ + self.NAME + " handling child  : " + class_name)
                child_schema = copy.deepcopy(self.schema)
                child_defaults = copy.deepcopy(self.defaults.get(class_name, OrderedDict()))

                if self.NAME in class_table:
                    if class_name in class_table[self.NAME] :
                        child = ManagedPlugin(name=class_name,
                                              schema = child_schema,
                                              defaults = child_defaults,
                                              connected_plugin = class_table[self.NAME][class_name])
                    else:
                        child = None
                    # When a connected manager is found, entries in defaults that do not have their corresponding plugin
                    # correctly instanced ( due, for example to a lacking required command) are not instanced
                    #     print("***********************************************************",class_name)
                    #     child = ManagedChoiceNode(name=class_name,
                    #                               schema=child_schema,
                    #                               defaults=child_defaults)
                else:
                    child = ManagedChoiceNode(name=class_name,
                                              schema=child_schema,
                                              defaults=child_defaults)

                # here we override child shema_name, as is neede to be different from instance class name
                # WARNING.... external set of member variable outside object methods
                if child:
                    child.schema_name=self.NAME
                    self.add_child(child)


class ConnectedManager(ManagerChoiceNode):

    def __init__(self, *args, **kwargs):
        super(ConnectedManager, self).__init__(*args, **kwargs)


        if 'children' in self.schema and hasattr(self.defaults, 'get'):
            for class_name in self.defaults:
                constructor_logger.debug(self.__class__.__name__ + self.NAME + " handling child  : " + class_name)
                if class_name in self.class_table:
                    connected_plugin = self.class_table[class_name]
                    plugin_params = self.class_table[class_name].PARAMS
                    child = ManagedPlugin(name=class_name,
                                          schema=copy.deepcopy(self.schema),
                                          defaults=copy.deepcopy(self.defaults.get(class_name, OrderedDict())),
                                          connected_plugin=self.class_table[class_name])
                    # here we override child shema_name, as is neede to be different from instance class name
                    # WARNING.... external set of member variable outside object methods
                    child.schema_name=self.NAME
                    self.add_child(child)

class ManagedPlugin(ManagedChoiceNode):

    def __init__(self, *args, **kwargs):
        """
        Node associated to a plugin class, on substitution, fill
        the member templates of the associated plugin
        """

        merged_defaults = copy.deepcopy(kwargs['defaults'])
        if merged_defaults == None:
            merged_defaults = OrderedDict()
        if 'connected_plugin' in kwargs:
            self.connected_plugin = kwargs['connected_plugin']
            if hasattr(self.connected_plugin, 'PARAMS'):
                if hasattr(self.connected_plugin.PARAMS, 'get'):
                    for param in self.connected_plugin.PARAMS:
                        constructor_logger.debug(self.__class__.__name__ + str(kwargs.get('name', self.NAME)) + " calling connected plugin " +
                                                self.connected_plugin.__class__.__name__ + " param " + str(param))
                        computed_param = self.connected_plugin.PARAMS[param]()
                        #computed_param = getattr(self.connected_plugin, self.connected_plugin.PARAMS[param])()
                        constructor_logger.info(self.__class__.__name__ + str(kwargs.get('name', self.NAME)) + " asking  connected plugin " +
                                                self.connected_plugin.__class__.__name__ + " param " + param +  " returned "+ str(computed_param))


                        merged_defaults[param] = self.connected_plugin.merge_list(merged_defaults.get(param, OrderedDict()),
                                                                                  computed_param)
        kwargs['defaults'] = merged_defaults
        super(ManagedPlugin, self).__init__(*args, **kwargs)

    def substitute(self,choices):
        self.connected_plugin.selected = True
        self.connected_plugin.templates=dict()
        active_templates=super(ManagedPlugin, self).substitute(choices)
        for templ in active_templates:
            self.connected_plugin.templates[templ] = active_templates[templ]
        return active_templates