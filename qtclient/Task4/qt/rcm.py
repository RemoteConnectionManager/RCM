import sys
from PyQt5.QtWidgets import QMainWindow, QDesktopWidget, QApplication
from main_widget import MainWidget


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle("Remote Connection Manager - CINECA")

        width = 600
        height = 200

        screen_width = QDesktopWidget().width()
        screen_height = QDesktopWidget().height()

        self.setGeometry((screen_width/2) - (width/2),
                         (screen_height/2) - (height/2),
                         width, height)

        mainW = MainWidget()
        self.setCentralWidget(mainW)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
