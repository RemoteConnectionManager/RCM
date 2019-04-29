import logging
import os
import sys
import pwd
import shutil
import datetime
import traceback

# set prefix.
current_file = os.path.realpath(os.path.expanduser(__file__))
current_prefix = os.path.dirname(os.path.dirname(current_file))
# current_etc_path = os.path.join(current_prefix, "etc")
#
#
# current_path = os.path.dirname(os.path.dirname(current_file))
# current_lib_path = os.path.join(current_path, "lib")
# sys.path.insert(0, current_path)
# sys.path.insert(0, current_lib_path)

import rcm


logger = logging.getLogger('rcmServer' + '.' + __name__)


class DbSessionManager:
    """
    This class takes care of all permanent storage (shared filesystem) operations, it mantains the storage associated
    with current sessions and takes care of removing the sessions when their associated job does not exist any more
    """

    def __init__(self):
        self.username = pwd.getpwuid(os.geteuid())[0]
        self.base_dir = os.path.expanduser("~%s/.rcm" % self.username)
        self.sessions_dir = os.path.abspath(os.path.join(self.base_dir, 'sessions'))
        self.old_sessions_dir = os.path.abspath(os.path.join(self.base_dir, 'old_sessions'))

    def allocate_session(self, tag=''):
        time_id = datetime.datetime.now().isoformat()
        session_id = tag + time_id.replace(':', '_')
        session_folder = os.path.join(self.sessions_dir, session_id)
        os.makedirs(session_folder)
        return session_id

    def session_folder(self, session_id):
        return os.path.join(self.sessions_dir, session_id)

    def session_file_path(self, session_id):
        return os.path.join(self.sessions_dir, session_id, 'session')

    def session_jobscript_path(self, session_id):
        return os.path.join(self.sessions_dir, session_id, 'job')

    def session_jobout_path(self, session_id):
        return os.path.join(self.sessions_dir, session_id, 'joblog')

    def write_jobscript(self, session_id, script):
        # write script on session_jobscript_path
        jobfile = self.session_jobscript_path(session_id)
        with open(jobfile, 'w') as f:
            f.write(script)
        return jobfile

    def sessions(self):
        sessions = {}
        if not os.path.isdir(self.sessions_dir):
            return sessions
        for sess_id in os.listdir(self.sessions_dir):
            sess_file = self.session_file_path(sess_id)
            if os.path.exists(sess_file):
                logger.debug("loading session from file: " + sess_file)
                try:
                    sessions[sess_id] = rcm.rcm_session(fromfile=sess_file)
                except Exception as e:
                    # print("WARNING: not valid session file %s: %s\n" % (file, e),type(inst),inst.args,file=sys.stderr)
                    sys.stderr.write("%s: %s RCM:EXCEPTION" % (format(e), traceback.format_exc()))

        return sessions

    def remove_session(self, sess_id):
        ses_folder = self.session_folder(sess_id)
        if not os.path.exists(ses_folder):
            logger.error("cleaning session id: " + sess_id + " MISSING SESSION FOLDER: " + ses_folder)
            return
        if not os.path.isdir(ses_folder):
            logger.error("cleaning session id: " + sess_id + " PATH: " + ses_folder + " NOT A FOLDER")
            return

        if not os.path.exists(self.old_sessions_dir):
            try:
                os.makedirs(self.old_sessions_dir)
            except Exception as e:
                sys.stderr.write("%s: %s CANNOT CREATE OLD SESSIONS FOLDER: %s" % (format(e),
                                                                                   traceback.format_exc(),
                                                                                   self.old_sessions_dir))
                return
        try:
            shutil.move(ses_folder, self.old_sessions_dir)
        except Exception as e:
            sys.stderr.write("%s: %s CANNOT MOVE SESSION FOLDER %s INTO OLD SESSIONS FOLDER: %s" %
                             (format(e), traceback.format_exc(), ses_folder, self.old_sessions_dir))
            return
        logger.info("session folder: " + ses_folder + " moved to " + self.old_sessions_dir)

        # cleaning old_sessions_dir
        old_sessions = [s for s in os.listdir(self.old_sessions_dir)
                        if os.path.isdir(os.path.join(self.old_sessions_dir, s))]
        old_sessions.sort(key=lambda s: os.path.getmtime(os.path.join(self.old_sessions_dir, s)))
        min_old_sessions = 5
        if len(old_sessions) > 2 * min_old_sessions:
            for s in old_sessions[:-min_old_sessions]:
                folder_to_remove = os.path.abspath(os.path.join(self.old_sessions_dir, s))
                logger.info("removing old session folder: " + folder_to_remove)
                # shutil.rmtree(folder_to_remove)

