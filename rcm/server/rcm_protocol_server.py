from __future__ import print_function
import os
import sys
import json

import rcm
from  logger_server import logger

class rcm_protocol:
    """
    This is the class that wraps remote procedures call protocol of RCM
    funcions are wrapped by protocol parser to produce the command line interface as well as by
    client rcm_protocol_client to expose a protocol class stub for remote call
    return data are objects efined in rcm, wrapped currently in pickle and packed on stdout
    """
    def __init__(self,rcm_server=None):
        if(rcm_server):
            self.rcm_server=rcm_server

    def config(self,build_platform=''):
        logger.debug("config")
        conf=rcm.rcm_config()
        if(build_platform):
            (check,url)=self.rcm_server.get_checksum(build_platform)
            conf.set_version(check,url)
        queueList = self.rcm_server.get_queue()
        for q in queueList:
            conf.add_queue(q)
        for vnc_id,menu_entry in self.rcm_server.pconfig.get_vnc_menu().items():
            conf.add_vnc(vnc_id,menu_entry)
        # ########## new interface ############
        jobscript_json_menu = self.rcm_server.pconfig.get_jobscript_json_menu()
        if jobscript_json_menu :
            conf.config['jobscript_json_menu']=jobscript_json_menu
        # #####################################
        conf.serialize()

    def config_xml(self,build_platform=''):
        logger = logging.getLogger("basic")    
        logger.debug("config_xml")

    def version(self,build_platform=''):
        logger.debug("version")
        print("get version")
        if (self.client_sendfunc):
            return self.client_sendfunc("version "+build_platform)


    def loginlist(self,subnet=''): 
        logger.debug("loginlist")
#	import socket
        self.rcm_server.subnet = subnet
#        fullhostname = socket.getfqdn()
        self.rcm_server.fill_sessions_hash()
        s=rcm.rcm_sessions()
        for sid, ses in list(self.rcm_server.sessions.items()):
            s.add_session(ses)
            #s.array.append(self.rcm_server.sessions[sid])
        s.write()

    def list(self,subnet=''): 
        logger.debug("list")
        self.rcm_server.subnet = subnet
        
        self.rcm_server.load_sessions()
        s=rcm.rcm_sessions()
        logger.debug("list run session ")
        for sid in self.rcm_server.sids['run']:
            s.add_session(self.rcm_server.sessions[sid])
        s.write()

    def new(self,geometry='',queue='',sessionname='',subnet='',vncpassword='',vncpassword_crypted='',vnc_id='', choices_string=''):
        logger.debug("new")
        if choices_string:
            print("choices string:", choices_string, file=sys.stderr)
            choices=json.loads(choices_string)
            res=self.rcm_server.pconfig.gui_composer.substitute(choices)

            for k, v in res.items():
                print(k, ":::>", file=sys.stderr)
                print(v, file=sys.stderr)
            return

        print("create new vnc display session")
        if(subnet): self.rcm_server.subnet = subnet
        if(queue): self.rcm_server.queue = queue
        if(sessionname): self.rcm_server.sessionname = sessionname
        if(vncpassword): self.rcm_server.vncpassword = vncpassword
        if(vncpassword_crypted): self.rcm_server.vncpassword_crypted = vncpassword_crypted
	
        self.rcm_server.substitutions['RCM_GEOMETRY'] = geometry	
        self.rcm_server.set_vnc_setup(vnc_id)
        new_session=self.rcm_server.execute_new()
        new_session.write()
    
    
    def kill(self,session_id=''): 
        logger.debug("kill")
        self.rcm_server.load_sessions()
        if(session_id):
            if session_id in self.rcm_server.sids['run']:
                jid=self.rcm_server.sessions[session_id].hash['jobid']
                self.rcm_server.kill_job(jid)
                file='%s/%s.session' % (self.rcm_server.get_rcmdirs()[0],session_id)
                c=rcm.rcm_session(fromfile=file)
                c.hash['state']='killing'
                c.serialize(file)
                c.write()
            else:
                sys.stderr.write("Not running session: %s\n" % (session_id))
                sys.stderr.flush()
                sys.exit(1)
