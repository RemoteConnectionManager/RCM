# python import
import json
import uuid
import os.path
import collections
from configparser import RawConfigParser

# pyqt5
from PyQt5.QtCore import QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QWidget, QFrame, QLabel, QComboBox, \
    QGridLayout, QVBoxLayout, QLineEdit, QHBoxLayout, QPushButton

# paramiko
from paramiko.ssh_exception import AuthenticationException

# local includes
from ssh import ssh_login
from display_dialog import QDisplayDialog
from pyinstaller_utils import resource_path
from logger import logger


class QSessionWidget(QWidget):
    """
    Create a new session widget to be put inside a tab in the main window
    For each session we can have many displays
    """

    # define a signal when the user successful log in
    logged_in = pyqtSignal(str)

    sessions_changed = pyqtSignal(collections.deque)

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)

        self.user = ""
        self.displays = {}

        self.config_file_name = os.path.join(os.path.expanduser('~'), '.rcm', 'RCM2.cfg')
        self.sessions_list = None
        self.parser = RawConfigParser()

        # widgets
        self.session_combo = QComboBox(self)
        self.host_line = QLineEdit(self)
        self.user_line = QLineEdit(self)
        self.pssw_line = QLineEdit(self)

        # containers
        self.containerLoginWidget = QWidget()
        self.containerSessionWidget = QWidget()

        # layouts
        self.session_ver_layout = QVBoxLayout()
        self.rows_ver_layout = QVBoxLayout()

        # icons
        self.connect_ico = QIcon()
        self.kill_ico = QIcon()
        self.share_ico = QIcon()

        self.init_ui()

        self.uuid = uuid.uuid4().hex

    def init_ui(self):
        """
        Initialize the interface
        """

    # Login Layout
    # grid login layout
        grid_login_layout = QGridLayout()

        # parse config file to load the most recent sessions
        if os.path.exists(self.config_file_name):
            try:
                with open(self.config_file_name, 'r') as config_file:
                    self.parser.read_file(config_file, source=self.config_file_name)
                    sessions_list = self.parser.get('LoginFields', 'hostList')
                    self.sessions_list = collections.deque(json.loads(sessions_list), maxlen=5)
            except:
                logger.error("Failed to load the sessions list from the config file")

        session_label = QLabel(self)
        session_label.setText('Sessions:')
        self.session_combo.clear()
        self.session_combo.addItems(self.sessions_list)

        self.session_combo.activated.connect(self.on_session_change)
        if self.sessions_list:
            self.session_combo.activated.emit(0)

        grid_login_layout.addWidget(session_label, 0, 0)
        grid_login_layout.addWidget(self.session_combo, 0, 1)

        host_label = QLabel(self)
        host_label.setText('Host:')

        grid_login_layout.addWidget(host_label, 1, 0)
        grid_login_layout.addWidget(self.host_line, 1, 1)

        user_label = QLabel(self)
        user_label.setText('User:')

        grid_login_layout.addWidget(user_label, 2, 0)
        pssw_label = QLabel(self)
        grid_login_layout.addWidget(self.user_line, 2, 1)

        pssw_label.setText('Password:')

        self.pssw_line.setEchoMode(QLineEdit.Password)
        grid_login_layout.addWidget(pssw_label, 3, 0)
        grid_login_layout.addWidget(self.pssw_line, 3, 1)

    # hor login layout
        pybutton = QPushButton('Login', self)
        pybutton.clicked.connect(self.login)
        pybutton.setShortcut("Return")

        login_hor_layout = QHBoxLayout()
        login_hor_layout.addStretch(1)
        login_hor_layout.addWidget(pybutton)
        login_hor_layout.addStretch(1)

    # login layout
        # it disappears when the user logged in
        login_layout = QVBoxLayout()
        login_layout.addLayout(grid_login_layout)
        login_layout.addLayout(login_hor_layout)

        self.containerLoginWidget.setLayout(login_layout)

    # Create the main layout
        new_tab_main_layout = QVBoxLayout()
        new_tab_main_layout.addWidget(self.containerLoginWidget)

    # Session Layout
        plusbutton_layout = QGridLayout()
        self.rows_ver_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_ver_layout.setSpacing(0)

        self.session_ver_layout.addLayout(plusbutton_layout)
        self.session_ver_layout.addLayout(self.rows_ver_layout)
        self.session_ver_layout.addStretch(1)

        self.connect_ico.addFile(resource_path('icons/connect.png'))
        self.kill_ico.addFile(resource_path('icons/kill.png'))
        self.share_ico.addFile(resource_path('icons/share.png'))

        font = QFont()
        font.setBold(True)

        name = QLabel()
        name.setText("Name")
        name.setFont(font)
        plusbutton_layout.addWidget(name, 0, 0)

        status = QLabel()
        status.setText("Status")
        status.setFont(font)
        plusbutton_layout.addWidget(status, 0, 1)

        time = QLabel()
        time.setText("Time")
        time.setFont(font)
        plusbutton_layout.addWidget(time, 0, 2)

        resources = QLabel()
        resources.setText("Resources")
        resources.setFont(font)
        plusbutton_layout.addWidget(resources, 0, 3)

        x = QLabel()
        x.setText("")
        plusbutton_layout.addWidget(x, 0, 4)
        plusbutton_layout.addWidget(x, 0, 5)

        new_display_ico = QIcon()
        new_display_ico.addFile(resource_path('icons/plus.png'), QSize(16, 16))

        new_display_btn = QPushButton()
        new_display_btn.setIcon(new_display_ico)
        new_display_btn.setToolTip('Create a new display session')
        new_display_btn.clicked.connect(self.add_new_display)

        new_display_layout = QHBoxLayout()
        new_display_layout.addSpacing(100)
        new_display_layout.addWidget(new_display_btn)

        plusbutton_layout.addLayout(new_display_layout, 0, 6)

        self.containerSessionWidget.setLayout(self.session_ver_layout)
        new_tab_main_layout.addWidget(self.containerSessionWidget)
        self.containerSessionWidget.hide()

        self.setLayout(new_tab_main_layout)

    def on_session_change(self):
        """
        Update the user and host fields when the user selects a different session in the combo
        :return:
        """
        try:
            user, host = self.session_combo.currentText().split('@')
            self.user_line.setText(user)
            self.host_line.setText(host)
        except ValueError:
            pass

    def login(self):
        session_name = str(self.user_line.text()) + "@" + str(self.host_line.text())

        try:
            logger.info("Logging into " + session_name)
            ssh_login(self.host_line.text(),
                      22,
                      self.user_line.text(),
                      self.pssw_line.text(),
                      'ls')
        except AuthenticationException:
            logger.error("Failed to login: invalid credentials")
            return

        logger.info("Logged in " + session_name)
        self.user = self.user_line.text()

        # update sessions list
        if session_name in list(self.sessions_list):
            self.sessions_list.remove(session_name)
        self.sessions_list.appendleft(session_name)

        self.sessions_changed.emit(self.sessions_list)

        # update config file
        self.update_config_file(session_name)

        # Hide the login view and show the session one
        self.containerLoginWidget.hide()
        self.containerSessionWidget.show()

        # Emit the logged_in signal.
        self.logged_in.emit(session_name)

    def add_new_display(self):
        # cannot have more than 5 sessions
        if len(self.displays) >= 5:
            logger.warning("You have already 5 displays")
            return

        display_win = QDisplayDialog(list(self.displays.keys()))
        display_win.setModal(True)

        if display_win.exec() != 1:
            return

        display_hor_layout = QHBoxLayout()
        display_hor_layout.setContentsMargins(0, 2, 0, 2)
        display_hor_layout.setSpacing(2)

        display_ver_layout = QVBoxLayout()
        display_ver_layout.setContentsMargins(0, 0, 0, 0)
        display_ver_layout.setSpacing(0)

        display_ver_layout.addLayout(display_hor_layout)

        display_widget = QWidget()
        display_widget.setLayout(display_ver_layout)

        id = display_win.display_name
        print(id)

        name = QLabel()
        name.setText(str(id)[:16])
        display_hor_layout.addWidget(name)

        status = QLabel()
        status.setText("Pending...")
        display_hor_layout.addWidget(status)

        time = QLabel()
        time.setText("24H")
        display_hor_layout.addWidget(time)

        resources = QLabel()
        resources.setText("1 Node")
        display_hor_layout.addWidget(resources)

        connect_btn = QPushButton()
        connect_btn.setIcon(self.connect_ico)
        connect_btn.setToolTip('Connect to the remote display')
        connect_btn.clicked.connect(lambda: self.connect_display(id))
        display_hor_layout.addWidget(connect_btn)

        share_btn = QPushButton()
        share_btn.setIcon(self.share_ico)
        share_btn.setToolTip('Share the remote display via file')
        share_btn.clicked.connect(lambda: self.share_display(id))
        display_hor_layout.addWidget(share_btn)

        kill_btn = QPushButton()
        kill_btn.setIcon(self.kill_ico)
        kill_btn.setToolTip('Kill the remote display')
        kill_btn.clicked.connect(lambda: self.kill_display(id))
        display_hor_layout.addWidget(kill_btn)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        display_ver_layout.addWidget(separator)

        self.rows_ver_layout.addWidget(display_widget)

        self.displays[id] = display_widget
        logger.info("Added new display")

    def update_config_file(self, session_name):
        """
        Update the config file with the new session name
        :param session_name: name of the last session inserted by the user
        :return:
        """
        if not self.parser.has_section('LoginFields'):
            self.parser.add_section('LoginFields')

        self.parser.set('LoginFields', 'hostList', json.dumps(list(self.sessions_list)))

        try:
            config_file_dir = os.path.dirname(self.config_file_name)
            if not os.path.exists(config_file_dir):
                os.makedirs(config_file_dir)

            with open(os.path.join(os.path.expanduser('~'), '.rcm', 'RCM2.cfg'), 'w') as config_file:
                self.parser.write(config_file)
        except:
            logger.error("failed to dump the session list in the configuration file")

    def connect_display(self, id):
        print(self.displays[id])
        logger.info("Connected to remote display " + str(id))

    def share_display(self, id):
        print(self.displays[id])
        logger.info("Shared display " + str(id))

    def kill_display(self, id):
        # first we hide the display
        logger.debug("Hiding display " + str(id))
        self.displays[id].hide()

        # then we remove it from the layout and the dictionary
        self.rows_ver_layout.removeWidget(self.displays[id])
        del self.displays[id]

        logger.info("Killed display " + str(id))