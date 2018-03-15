from PyQt5.QtWidgets import QPushButton, \
    QWidget, QLineEdit, QVBoxLayout, QHBoxLayout,\
    QGridLayout, QLabel, QComboBox, QFileDialog

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

from ssh import sshCommando
from paramiko.ssh_exception import AuthenticationException

class QSessionWidget(QWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.hosts = ["login.marconi.cineca.it", "login.pico.cineca.it"]
        self.user = ""
        self.rows = []
    # Create first tab
        new_tab_main_layout = QVBoxLayout()

    # Login Layout
        grid_login_layout = QGridLayout()
        login_layout = QVBoxLayout()

        host_label = QLabel(self)
        host_label.setText('Host:')
        self.host_combo = QComboBox(self)
        self.host_combo.addItems(["login.marconi.cineca.it", "login.pico.cineca.it"])
        grid_login_layout.addWidget(host_label, 0, 0)
        grid_login_layout.addWidget(self.host_combo, 0, 1)

        user_label = QLabel(self)
        user_label.setText('User:')
        self.user_line = QLineEdit(self)
        grid_login_layout.addWidget(user_label, 1, 0)
        grid_login_layout.addWidget(self.user_line, 1, 1)

        pssw_label = QLabel(self)
        pssw_label.setText('Password:')
        self.pssw_line = QLineEdit(self)
        self.pssw_line.setEchoMode(QLineEdit.Password)
        grid_login_layout.addWidget(pssw_label, 2, 0)
        grid_login_layout.addWidget(self.pssw_line, 2, 1)

        login_hor_layout = QHBoxLayout()
        pybutton = QPushButton('Login', self)
        pybutton.clicked.connect(self.login)

        openbtn = QPushButton('Open', self)
        openbtn.clicked.connect(self.open)

        login_hor_layout.addStretch(1)
        login_hor_layout.addWidget(openbtn)
        login_hor_layout.addWidget(pybutton)
        login_hor_layout.addStretch(1)

        self.error_label = QLabel(self)
        self.error_label.setText("Wrong username or password")
        self.error_label.setStyleSheet("color:red")
        grid_login_layout.addWidget(self.error_label, 3, 1)
        self.error_label.hide()

        login_layout.addLayout(grid_login_layout)
        login_layout.addLayout(login_hor_layout)
        self.containerLoginWidget = QWidget()
        self.containerLoginWidget.setLayout(login_layout)
        new_tab_main_layout.addWidget(self.containerLoginWidget)

    # Session Layout
        plusbutton_layout = QHBoxLayout()
        self.session_ver_layout = QVBoxLayout()
        self.rows_ver_layout = QVBoxLayout()
        self.rows_ver_layout.setContentsMargins(0,0,0,0)
        self.rows_ver_layout.setSpacing(0)

        self.session_ver_layout.addLayout(plusbutton_layout)
        self.session_ver_layout.addLayout(self.rows_ver_layout)
        self.session_ver_layout.addStretch(1)

        self.connect_ico = QIcon()
        self.connect_ico.addFile('icons/connect.png')

        self.kill_ico = QIcon()
        self.kill_ico.addFile('icons/kill.png')

        self.share_ico = QIcon()
        self.share_ico.addFile('icons/share.png')

        name = QLabel()
        name.setText("Name")
        plusbutton_layout.addWidget(name)

        status = QLabel()
        status.setText("Status")
        plusbutton_layout.addWidget(status)

        time = QLabel()
        time.setText("Time")
        plusbutton_layout.addWidget(time)

        resources = QLabel()
        resources.setText("Resources")
        plusbutton_layout.addWidget(resources)

        new_display_ico = QIcon()
        new_display_ico.addFile('icons/plus.png', QSize(16, 16))
        new_display = QPushButton()
        new_display.setIcon(new_display_ico)
        new_display.clicked.connect(self.addNewDisplay)
        plusbutton_layout.addStretch(1)
        plusbutton_layout.addWidget(new_display)

        self.containerSessionWidget = QWidget()
        self.containerSessionWidget.setLayout(self.session_ver_layout)
        new_tab_main_layout.addWidget(self.containerSessionWidget)
        self.containerSessionWidget.hide()

        self.setLayout(new_tab_main_layout)

    def login(self):
        try:
            sshCommando(self.host_combo.currentText(), 22,
                        self.user_line.text(),
                        self.pssw_line.text(), 'ls')
        except AuthenticationException:
            self.error_label.show()
            print(self.error_label)
            return
        self.user = self.user_line.text()
        self.containerLoginWidget.hide()
        self.containerSessionWidget.show()

    def open(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileName(self, "Apri...", "",
                                                      "VNC Files (*.vnc);;All Files (*)", options=options)
        if filename:
                print(filename)

    def addNewDisplay(self):

        if len(self.rows) >= 5:
            return

        display_hor_layout = QHBoxLayout()
        display_hor_layout.setContentsMargins(0,2,0,0)
        display_hor_layout.setSpacing(2)

        name = QLabel()
        name.setText("Carlo")
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

        connect = QPushButton()
        connect.setIcon(self.connect_ico)
        display_hor_layout.addWidget(connect)

        share = QPushButton()
        share.setIcon(self.share_ico)
        display_hor_layout.addWidget(share)

        kill = QPushButton()
        kill.setIcon(self.kill_ico)
        display_hor_layout.addWidget(kill)

        display_widget = QWidget()
        display_widget.setLayout(display_hor_layout)

        #self.rows_ver_layout.addLayout(display_hor_layout)

        self.rows_ver_layout.addWidget(display_widget)
        self.rows.append(display_widget)