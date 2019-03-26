import logging
import logging.config
import importlib
import os
import json
import socket
import pwd
import copy
from collections import OrderedDict

# set prefix.
current_file = os.path.realpath(os.path.expanduser(__file__))
current_prefix = os.path.dirname(os.path.dirname(current_file))
current_etc_path = os.path.join(current_prefix, "etc")

import sys
current_path = os.path.dirname(os.path.dirname(current_file))
current_lib_path = os.path.join(current_path, "lib")
sys.path.insert(0, current_path)
sys.path.insert(0, current_lib_path)

# local import
import config
import jobscript_builder
import db
#import manager
import scheduler
from external import hiyapyco

import rcm
import enumerate_interfaces
import utils


logger = logging.getLogger('rcmServer' + '.' + __name__)

class ServerManager:
    """
    The manager class.
    It is responsible to load from file the scheduler and service plugins.
    List of schedulers and services is written in a configuration yaml file
    """

    def __init__(self):
        self.schedulers = dict()
        self.services = dict()
        self.downloads = dict()
        self.root_node = None
        self.session_manager = db.DbSessionManager()
        self.login_fullname=''
        self.network_map = dict()

    def init(self):
        self.username = pwd.getpwuid(os.geteuid())[0]
        self.login_fullname = socket.getfqdn()


        self.configuration = config.getConfig('default')

        logging.config.dictConfig(self.configuration['logging_configs'])

        # load client download info
        self.downloads = self.configuration['download']



        # load plugins
        for scheduler_str in self.configuration['plugins', 'schedulers']:
            print(scheduler_str)
            try:
                module_name, class_name = scheduler_str.rsplit(".", 1)
                scheduler_class = getattr(importlib.import_module(module_name), class_name)
                scheduler_obj = scheduler_class()
                self.schedulers[scheduler_obj.NAME] = scheduler_obj
                logger.info('loaded scheduler plugin ' +
                             scheduler_obj.__class__.__name__ +
                             " - " + scheduler_obj.NAME)
            except Exception as e:
                logger.error("plugin " + scheduler_str + " loading failed")
                logger.error(e)

        # load services
        for service_str in self.configuration['plugins', 'services']:
            try:
                module_name, class_name = service_str.rsplit(".", 1)
                service_class = getattr(importlib.import_module(module_name), class_name)
                service_obj = service_class()
                self.services[service_obj.NAME] = service_obj
                logger.info('loaded service plugin ' + service_obj.__class__.__name__ + " - " + service_obj.NAME)
            except Exception as e:
                logger.error("plugin loading failed")
                logger.error(e)

        # instantiate widget tree
        jobscript_builder.class_table = {'SCHEDULER' :  self.schedulers,
                                         'COMMAND' :    self.services,
                                        }

        self.root_node = jobscript_builder.AutoChoiceNode(name='TOP')


    def map_login_name(self, subnet, nodelogin):
        logger.debug("mapping login " + nodelogin + " on network " + subnet)
        return self.configuration['network', subnet].get(nodelogin, nodelogin)

    def get_login_node_name(self, subnet=''):
        logger.debug("get_login")

        if (subnet):
            nodelogin = enumerate_interfaces.external_name(subnet)
            if (not nodelogin):
                nodelogin = self.login_fullname
            nodelogin = self.map_login_name(subnet, nodelogin)
            return nodelogin
        else:
            return self.login_fullname

    def get_checksum_and_url(self, build_platform):
        logger.debug("searching platform " + str(build_platform) + " into " + str(self.downloads))
        checksum = ""
        downloadurl = ""
        for checksum, urls in self.downloads.get(build_platform, OrderedDict()).items() :
            for downloadurl in urls:
                logger.debug("checksum: " + checksum + " url: " + downloadurl)

        return checksum, downloadurl

    def get_jobscript_json_menu(self):
        return json.dumps(self.root_node.get_gui_options())

    def handle_choices(self,choices_string):
        choices=json.loads(choices_string)

        # set all plugins to unselected
        for plugin_collections in [self.schedulers, self.services]:
            for plug_name, plug_obj in plugin_collections.items():
                plug_obj.selected = False

        # call root node substitutions, as side effect, it select active plugins
        self.top_templates = self.root_node.substitute(choices)


        # here we find which scheduler has been selected.
        self.active_scheduler = None
        for sched_name,sched_obj in self.schedulers.items():
            if sched_obj.selected:
                self.active_scheduler = sched_obj
                break

        # here we find which service has been selected.
        self.active_service = None
        for service_name,service_obj in self.services.items():
            if service_obj.selected:
                self.active_service = service_obj
                break


    def new_session(self,
            sessionname='',
            subnet='',
            vncpassword='',
            vncpassword_crypted=''):
        session_id = self.session_manager.new_session(tag=self.active_scheduler.NAME)
        new_session = rcm.rcm_session(sessionid=session_id,
                                      state='init',
                                      username=self.username,
                                      sessionname=sessionname,
                                      nodelogin=self.login_fullname,
                                      vncpassword=vncpassword_crypted)
        print("####### session #####\n", new_session.get_string(format='json'))
        new_session.serialize(self.session_manager.session_file_path(session_id))

        print("login_name: ", self.get_login_node_name())
        printout = "============submitting "
        if self.active_service :
            printout += "service: " + self.active_service.NAME
        if self.active_scheduler :
            printout +=  " with scheduler: " + self.active_scheduler.NAME
        print(printout)

        substitutions = {'RCM_SESSIONID': str(session_id),
                         'RCM_SESSION_FOLDER': self.session_manager.session_folder(session_id),
                         'RCM_JOBLOG': self.session_manager.session_jobout_path(session_id)}


        # assembly job script
        script = self.top_templates.get('SCRIPT', 'No script in templates')
        script = utils.stringtemplate(script).safe_substitute(substitutions)
        print("@@@@@@@@@@ script @@@@@@@@@\n" + script)

        service_logfile = self.top_templates.get('SERVICE.COMMAND.LOGFILE', '')
        service_logfile = utils.stringtemplate(service_logfile).safe_substitute(substitutions)
        print("@@@@@@@@@@ service_logfile @@@@@@@@@\n" + service_logfile)



        jobfile = self.session_manager.write_jobscript(session_id, script)
        jobid = self.active_scheduler.submit(jobfile=jobfile)

        # set status and jobid in curent session and write on disk
        new_session.hash['state'] = 'pending'
        new_session.hash['jobid'] = jobid
        new_session.serialize(self.session_manager.session_file_path(session_id))
        print("####### serialized session #####\n" + new_session.get_string(format='json'))

        node,port  = self.active_service.search_port(service_logfile)
        new_session.hash['state'] = 'valid'
        new_session.hash['port'] = port
        new_session.hash['node'] = node
        print("####### serialized session #####\n" + new_session.get_string(format='json'))

        return session_id
