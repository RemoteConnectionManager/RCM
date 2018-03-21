import sys,logging
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, \
    QWidget,QTabWidget, QVBoxLayout, \
    QLabel, QFrame, QDesktopWidget
from PyQt5.QtCore import pyqtSlot
from session_widget import QSessionWidget
from logger import QLabelLogger,logger

class RCM(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Remote Connection Manager - CINECA - v0.01_alpha")

        width = 1000
        height = 300

        screen_width = QDesktopWidget().width()
        screen_height = QDesktopWidget().height()

        self.setGeometry((screen_width / 2) - (width / 2),
                         (screen_height / 2) - (height / 2),
                         width, height)

        self.setFixedHeight(height)
        self.setFixedWidth(width)

        self.main_widget = MainWidget(self)
        self.setCentralWidget(self.main_widget)

        logger.warning("Showing window")
        self.show()

class MainWidget(QWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.main_layout = QVBoxLayout(self)

    # Initialize tab screen
        self.tabs = QTabWidget()
        self.tabs.resize(300, 200)
        self.tabs_list = []
    # Add tabs
        self.addNewTab("Login...")
        self.addNewTab("+")
        self.tabs.currentChanged.connect(self.onChange)

    # Add tabs to widget
        self.main_layout.addWidget(self.tabs)

    #Add text_log
        text_log_label = QLabel(self)
        text_log_label.setText('Text Log')
        text_log_label.setFrameShape(QFrame.Panel)
        text_log_label.setFrameShadow(QFrame.Sunken)
        text_log_label.setLineWidth(1)
        text_log_handler = QLabelLogger(text_log_label)
        logger.addHandler(text_log_handler)
        self.main_layout.addWidget(text_log_label)

    #Set main layout
        self.setLayout(self.main_layout)

    @pyqtSlot()
    def onChange(self):
        if self.tabs.currentIndex() == self.tabs.count() - 1:
            self.tabs.setTabText(self.tabs.currentIndex(), "Login...")
            self.addNewTab("+")

    def addNewTab(self, session_name):
    #Add tab and set title
        self.tabs_list.append(QSessionWidget(self.tabs))
        self.tabs.addTab(self.tabs_list[self.tabs.count()], session_name)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RCM()
    sys.exit(app.exec_())

