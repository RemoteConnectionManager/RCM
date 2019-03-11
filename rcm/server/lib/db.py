import logging
import os
import sys
import pwd
import datetime

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



class DbSessionManager:
    """
    This class takes care of all permanent storage (shared filesystem) operations, it mantains the storage associated
    with current sessions and takes care of removing the sessions when their associated job does not exist any more
    """

    def __init__(self):
        self.username = pwd.getpwuid(os.geteuid())[0]
        self.base_dir = os.path.expanduser("~%s/.rcm" % (self.username))
        self.sessions_dir = os.path.abspath(os.path.join(self.base_dir, 'sessions'))

    def new_session(self,tag=''):
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



