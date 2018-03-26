# std lib
import sys

# pyqt5
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QApplication, \
    QWidget, QTabWidget, QVBoxLayout, \
    QLabel, QFrame, QDesktopWidget

# local includes
from session_widget import QSessionWidget
from logger import QLabelLogger, logger


class RCMMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Remote Connection Manager - CINECA - v0.01_alpha")
        logger.debug("QMainWindow created")

        width = 1000
        height = 300

        screen_width = QDesktopWidget().width()
        screen_height = QDesktopWidget().height()

        self.setGeometry((screen_width / 2) - (width / 2),
                         (screen_height / 2) - (height / 2),
                         width, height)

        self.setFixedHeight(height)
        self.setFixedWidth(width)
        logger.debug("QMainWindow moved at the center of the screen")

        self.main_widget = MainWidget(self)
        self.setCentralWidget(self.main_widget)
        logger.debug("MainWidget created and added to QMainWindow")


class MainWidget(QWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)

        self.init_ui()

    def init_ui(self):
        """
        Initialize the interface
        """

        self.main_layout = QVBoxLayout(self)

    # Initialize tab screen
        self.tabs = QTabWidget()
        self.tabs.resize(300, 200)
        self.tabs_list = []
        logger.debug("Initialized tab screen")

    # Add tabs
        self.add_new_tab("Login...")
        self.add_new_tab("+")
        self.tabs.currentChanged.connect(self.on_change)
        logger.debug("Created tabs")

    # Add tabs to widget
        self.main_layout.addWidget(self.tabs)
        logger.debug("Added tabs to widget")

    # Add text_log
        text_log_label = QLabel(self)
        text_log_label.setText('Text Log')
        text_log_label.setFrameShape(QFrame.Panel)
        text_log_label.setFrameShadow(QFrame.Sunken)
        text_log_label.setLineWidth(1)
        logger.debug("Added Log Label")
        text_log_handler = QLabelLogger(text_log_label)
        logger.addHandler(text_log_handler)
        logger.debug("Set the log handler")
        self.main_layout.addWidget(text_log_label)

    # Set main layout
        self.setLayout(self.main_layout)

    @pyqtSlot()
    def on_change(self):
        if self.tabs.currentIndex() == self.tabs.count() - 1:
            self.tabs.setTabText(self.tabs.currentIndex(), "Login...")
            self.add_new_tab("+")

    def add_new_tab(self, session_name):
    # Add tab and set title
        self.tabs_list.append(QSessionWidget(self.tabs))
        self.tabs.addTab(self.tabs_list[self.tabs.count()], session_name)
        logger.debug("Added new tab")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    rcm_win = RCMMainWindow()
    rcm_win.show()
    sys.exit(app.exec_())

