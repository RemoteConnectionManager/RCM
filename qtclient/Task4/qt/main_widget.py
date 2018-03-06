from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QLabel,QFileDialog
from login_dlg import LoginWindow


class MainWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)

        self.init_ui()

    def init_ui(self):
        grid_layout = QGridLayout()
        login = QPushButton('Login', self)
        login.clicked.connect(self.login)
        login.setFixedHeight(100)
        login.setFixedWidth(100)
        grid_layout.addWidget(login, 0, 0)

        open = QPushButton('Open', self)
        open.clicked.connect(self.open)
        open.setFixedHeight(100)
        open.setFixedWidth(100)
        grid_layout.addWidget(open, 1, 0)


        random_label=QLabel(self)
        random_label.setText('test')
        random_label.setFixedHeight(50)
        grid_layout.addWidget(random_label,0,1,2,1)
        random_label2=QLabel(self)
        random_label2.setText('test2')
        grid_layout.addWidget(random_label2,1,1)
        grid_layout.setColumnStretch(1, 5)


        self.setLayout(grid_layout)

    def login(self):
        logWin = LoginWindow()
        logWin.setModal(True)
        logWin.exec()

    def open(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "Apri...", "",
                                                      "All Files (*);;Python Files (*.vnc)", options=options)
        if fileName:
                print(fileName)

        def openFileNamesDialog(self):
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            files, _ = QFileDialog.getOpenFileNames(self, "Apri...", "",
                                                    "All Files (*);;Python Files (*.vnc)", options=options)
            if files:
                print(files)

