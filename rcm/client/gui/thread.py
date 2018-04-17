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


class ReloadThread(QThread):
    def __init__(self):
        QThread.__init__(self)

    def run(self):
        import time
        time.sleep(5)
