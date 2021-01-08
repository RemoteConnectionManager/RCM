#
# Copyright (c) 2014-2019 CINECA.
#
# This file is part of RCM (Remote Connection Manager) 
# (see http://www.hpc.cineca.it/software/rcm).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from PyQt5.QtCore import QThread, Qt,pyqtSignal
import traceback

# local includes
from client.miscellaneous.logger import logger
from client.utils.rcm_enum import Status


class LoginThread(QThread):

    prompt=pyqtSignal(str)

    def __init__(self, session_widget, host, user, password, preload=''):
        QThread.__init__(self)

        self.session_widget = session_widget
        self.host = host
        self.user = user
        self.password = password
        self.preload=preload


    def run(self):
        try:
            self.session_widget.remote_connection_manager.login_setup(host=self.host,
                                                                      user=self.user,
                                                                      password=self.password,
                                                                      preload=self.preload)

            self.session_widget.platform_config = self.session_widget.remote_connection_manager.get_config()
            self.session_widget.is_logged = True
        except Exception as e:
            self.session_widget.is_logged = False
            logger.error("Failed to login")
            logger.error(str(e) + " - " + str(traceback.format_exc()))


class KillThread(QThread):
    def __init__(self, session_widget, session, display_widget, current_status):
        QThread.__init__(self)
        self.session_widget = session_widget
        self.session = session
        self.display_widget = display_widget
        self.current_status = current_status

    def run(self):
        try:
            self.session_widget.remote_connection_manager.kill(self.session)
            self.display_widget.status = Status.FINISHED
        except Exception as e:
            self.display_widget.status = self.current_status
            logger.error("Failed to kill the display session")
            logger.error(e)


class ReloadThread(QThread):
    def __init__(self, session_widget):
        QThread.__init__(self)
        self.session_widget = session_widget

    def run(self):
        try:
            self.session_widget.display_sessions = self.session_widget.remote_connection_manager.list()
        except Exception as e:
            logger.error("Failed to reload the display sessions")
            logger.error(e)
            exc_info = (type(e), e, e.__traceback__)
            logger.error('Exception occurred', exc_info=exc_info)


