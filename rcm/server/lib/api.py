# std import
import sys
import logging
import traceback
import json

# local import
import rcm

logger = logging.getLogger('rcmServer' + '.' + __name__)


class ServerAPIs:
    """
    Class containing the server APIs. Same role as View in the MVC pattern.
    Features implemented are:
      - get the server configuration
      - get the api version
      - get the list of sessions
      - get the list of login nodes to which the client can connect to
      - create a new session
      - kill a session
    """

    api_version = "1.0.0"

    def __init__(self):
        self.server_manager = None

    def _server_init(self, client_info=None):
        if self.server_manager is None:
            import manager
            import config
            config.getConfig()
            self.server_manager = manager.ServerManager()
            self.server_manager.init(client_info)

    def config(self, build_platform='', client_current_version='', client_current_checksum=''):
        logger.debug("platform string" + str(build_platform) )
        platform_info = ''
        client_info = dict()
        if build_platform:
            print("#### build_platform:" + str(build_platform))
            if '{' == build_platform[0]:
                # interpreting build_platfrm as a json encodef pack_info field
                try:
                    client_info = json.loads(build_platform)
                    platform_info = client_info['platform']
                    client_current_version = client_info['version']
                    client_current_checksum = client_info['checksum']
                except Exception as e:
                    logger.info("error in handling json encoded pack_info, Exception: " +
                            str(e) + " - " + str(traceback.format_exc()))
            else:
                platform_info = build_platform 

        self._server_init(client_info)
        logger.debug("calling api config")
        conf = rcm.rcm_config()
        if platform_info:
            (checksum, url) = self.server_manager.get_checksum_and_url(platform_info,
                                                                       client_current_version=client_current_version,
                                                                       client_current_checksum=client_current_checksum)
            conf.set_version(checksum, url)
        jobscript_json_menu = self.server_manager.get_jobscript_json_menu()
        if jobscript_json_menu:
            conf.config['jobscript_json_menu'] = jobscript_json_menu

        queues = self.server_manager.configuration['old_client', 'queue_entries']
        for q in queues:
            conf.add_queue(q)
        for vnc in self.server_manager.configuration['old_client', 'vnc_entries']:
            conf.add_vnc(vnc, vnc + ' Description')
        conf.serialize()

    def version(self):
        self._server_init()
        logger.debug("calling api version")
        sys.stdout.write(rcm.serverOutputString + self.api_version)

    def loginlist(self, subnet=''):
        self._server_init()
        logger.debug("calling api loginlist")
        out_sessions = self.server_manager.map_sessions(self.server_manager.session_manager.sessions(), subnet)
        out_sessions.write()

    def list(self, subnet=''):
        self._server_init()
        logger.debug("calling api list")
        out_sessions = self.server_manager.map_sessions(self.server_manager.extract_running_sessions(), subnet)
        out_sessions.write()

    def new(self, geometry='',
            queue='',
            sessionname='',
            subnet='',
            vncpassword='',
            vncpassword_crypted='',
            vnc_id='',
            choices_string=''):
        self._server_init()
        logger.debug("calling api new")
        if not choices_string:
            choices_array = {}
            try:
                choices_array["SERVICE.COMMAND.WM.XSIZE"], choices_array["SERVICE.COMMAND.WM.YSIZE"] = geometry.split('x')
            except Exception as e:
                logger.warning("Exception: " + str(e) + " in handling geometry: " + geometry )

            for par,par_key in [(queue, 'queue_entries'), (vnc_id, 'vnc_entries')]:
                setup_dict = self.server_manager.configuration['old_client', par_key, par]
                choices_array.update(setup_dict)
            choices_string = json.dumps(choices_array)
            
        # sys.stderr.write("----choices string:::>"+ choices_string + "<:::\n")
        self.server_manager.handle_choices(choices_string)
        for k, v in self.server_manager.top_templates.items():
            logger.debug(k + " :::>\n" + str(v) + "\n<:")

        try:
            new_session = self.server_manager.create_session(
                sessionname=sessionname,
                subnet=subnet,
                vncpassword=vncpassword,
                vncpassword_crypted=vncpassword_crypted)
        except Exception as e:
            logger.warning("Exception: " + str(e) + " in job submission" )
            sys.stderr.write("Job submission error: " + str(e) )
            sys.stderr.flush()
            sys.exit(1)

        return_session = self.server_manager.map_session(new_session, subnet)
        return_session.write()
        return

    def kill(self, session_id=''):
        self._server_init()
        logger.debug("calling api kill")
        db_sessions = self.server_manager.session_manager
        if session_id:
            active_sessions = self.server_manager.extract_running_sessions()
            if session_id in active_sessions:
                ses = active_sessions[session_id]
                scheduler_name = ses.hash.get('scheduler', '')
                scheduler = self.server_manager.schedulers.get(scheduler_name, None)
                if scheduler:
                    jobid = ses.hash.get('jobid', '')
                    if scheduler.kill_job(jobid):
                        ses.hash['state'] = 'killing'
                        ses.serialize(db_sessions.session_file_path(session_id))
                        ses.write()
                    else:
                        sys.stderr.write("Scheduler: " + scheduler_name + " NOT DEFINED in " + str(
                            self.server_manager.schedulers.keys()))
                        sys.stderr.flush()
                        sys.exit(1)
                else:
                    sys.stderr.write("Not running session: %s\n" % (session_id))
                    sys.stderr.flush()
                    sys.exit(1)
            else:
                sys.stderr.write("Not existing session: %s\n" % (session_id))
                sys.stderr.flush()
                sys.exit(1)
