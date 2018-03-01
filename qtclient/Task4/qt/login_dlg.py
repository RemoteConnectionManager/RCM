from PyQt5.QtWidgets import QLabel, QLineEdit, QDialog, QComboBox, QHBoxLayout, \
    QVBoxLayout, QGroupBox, QGridLayout, QPushButton
from ssh import sshCommando


class LoginWindow(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setWindowTitle("Login")
        self.init_ui()

    def init_ui(self):
        grid_layout = QGridLayout()

        host_label = QLabel(self)
        host_label.setText('Host:')
        self.host_combo = QComboBox(self)
        self.host_combo.addItems(["login.marconi.cineca.it",
                                  "login.pico.cineca.it"])
        grid_layout.addWidget(host_label, 0, 0)
        grid_layout.addWidget(self.host_combo,0, 1)

        user_label = QLabel(self)
        user_label.setText('User:')
        self.user_line= QLineEdit(self)
        grid_layout.addWidget(user_label, 1, 0)
        grid_layout.addWidget(self.user_line, 1, 1)

        pssw_label = QLabel(self)
        pssw_label.setText('Password:')
        self.pssw_line = QLineEdit(self)
        self.pssw_line.setEchoMode(QLineEdit.Password)
        grid_layout.addWidget(pssw_label, 2, 0)
        grid_layout.addWidget(self.pssw_line, 2, 1)

        hor_layout = QHBoxLayout()
        pybutton = QPushButton('Login', self)
        pybutton.clicked.connect(self.login)
        hor_layout.addStretch(1)
        hor_layout.addWidget(pybutton)
        hor_layout.addStretch(1)

        group_box = QGroupBox("Please enter your credentials: ")
        group_box.setLayout(grid_layout)

        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(group_box)
        dialog_layout.addSpacing(10)
        dialog_layout.addLayout(hor_layout)
        self.setLayout(dialog_layout)

    def login(self):
        sshCommando(self.host_combo.currentText(), 22,
                    self.user_line.text(), self.pssw_line.text(),'ls')
