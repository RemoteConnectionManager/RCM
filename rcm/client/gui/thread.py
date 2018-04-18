# pyqt5
from PyQt5.QtCore import QThread


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
        except:
            self.session_widget.is_logged = False


class KillThread(QThread):
    def __init__(self, session_widget, session):
        QThread.__init__(self)
        self.session_widget = session_widget
        self.session = session

    def run(self):
        self.session_widget.remote_connection_manager.kill(self.session)


class ReloadThread(QThread):
    def __init__(self, session_widget):
        QThread.__init__(self)
        self.session_widget = session_widget

    def run(self):
        self.session_widget.display_sessions = self.session_widget.remote_connection_manager.list()
