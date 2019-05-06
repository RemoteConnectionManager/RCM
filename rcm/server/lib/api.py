# std import
import sys
import logging

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

    def __init__(self):
        self.server_manager = None

    def _server_init(self):
        if self.server_manager is None:
            import manager
            import config
            config.getConfig()
            self.server_manager = manager.ServerManager()
            self.server_manager.init()

    def config(self, build_platform='', client_current_version='', client_current_checksum=''):
        self._server_init()
        logger.debug("calling api config")
        conf = rcm.rcm_config()
        if build_platform:
            (checksum, url) = self.server_manager.get_checksum_and_url(build_platform,
                                                                       client_current_version=client_current_version,
                                                                       client_current_checksum=client_current_checksum)
            conf.set_version(checksum, url)
        jobscript_json_menu = self.server_manager.get_jobscript_json_menu()
        if jobscript_json_menu:
            conf.config['jobscript_json_menu'] = jobscript_json_menu
        conf.serialize()

    def version(self, build_platform=''):
        self._server_init()
        logger.debug("calling api version")

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
        if choices_string:
            # sys.stderr.write("----choices string:::>"+ choices_string + "<:::\n")
            self.server_manager.handle_choices(choices_string)
            for k, v in self.server_manager.top_templates.items():
                logger.debug(k + " :::>\n" + str(v) + "\n<:")

            new_session = self.server_manager.create_session(sessionname=sessionname,
                                                             subnet=subnet,
                                                             vncpassword=vncpassword,
                                                             vncpassword_crypted=vncpassword_crypted)

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
