import sys
from PyQt5.QtWidgets import QMainWindow, QDesktopWidget, QPushButton, QApplication
from login_dlg import LoginWindow


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.setWindowTitle("Remote Connection Manager - CINECA")
        width = 320
        height = 160

        screen_width = QDesktopWidget().width()
        screen_height = QDesktopWidget().height()

        self.setGeometry((screen_width/2) - (width/2),
                         (screen_height/2) - (height/2),
                         width, height)

        pybutton = QPushButton('Login', self)
        pybutton.clicked.connect(self.login)
        pybutton.resize(200, 32)
        pybutton.move(80, 40)

    def login(self):
        logWin = LoginWindow()
        logWin.setModal(True)
        logWin.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
