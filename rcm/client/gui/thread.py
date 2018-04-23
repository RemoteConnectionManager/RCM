# pyqt5
from PyQt5.QtCore import QThread

# local includes
from client.log.logger import logger
from client.utils.rcm_enum import Status


class LoginThread(QThread):
    def __init__(self, session_widget, host, user, password):
        QThread.__init__(self)

        self.session_widget = session_widget
        self.host = host
        self.user = user
        self.password = password

    def run(self):
        try:
            self.session_widget.remote_connection_manager.login_setup(host=self.host,
                                                                      remoteuser=self.user,
                                                                      password=self.password)
            self.session_widget.platform_config = self.session_widget.remote_connection_manager.get_config()
            self.session_widget.is_logged = True
        except Exception as e:
            self.session_widget.is_logged = False
            logger.error("Failed to login")
            logger.error(e)


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
