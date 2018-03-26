# std lib
import sys

# pyqt5
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QApplication, \
    QWidget, QTabWidget, QVBoxLayout, \
    QLabel, QFrame, QDesktopWidget, QAction, QFileDialog

# local includes
from session_widget import QSessionWidget
from pyinstaller_utils import resource_path
from logger import QLabelLoggerHandler, logger


class RCMMainWindow(QMainWindow):

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

        # Create new action
        new_action = QAction(QIcon(resource_path('icons/new.png')), '&New', self)
        new_action.setShortcut('Ctrl+N')
        new_action.setStatusTip('New VNC session')
        new_action.triggered.connect(self.new_vnc_session)

        # Create new action
        open_action = QAction(QIcon(resource_path('icons/open.png')), '&Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Open VNC session')
        open_action.triggered.connect(self.open_vnc_session)

        # Create exit action
        exit_action = QAction(QIcon(resource_path('icons/exit.png')), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.exit)

        # Create the settings action
        edit_settings_action = QAction('&Settings', self)
        edit_settings_action.setShortcut('Ctrl+S')
        edit_settings_action.setStatusTip('Custom the application settings')
        edit_settings_action.triggered.connect(self.edit_settings)

        # Create the about action
        about_action = QAction('&About', self)
        about_action.setShortcut('Ctrl+A')
        about_action.setStatusTip('About the application')
        about_action.triggered.connect(self.about)

        # Create the toolbar and add actions
        tool_bar = self.addToolBar("File")
        tool_bar.addAction(new_action)
        tool_bar.addAction(open_action)

        # Create menu bar and add actions
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(exit_action)
        edit_menu = menu_bar.addMenu('&Edit')
        edit_menu.addAction(edit_settings_action)
        help_menu = menu_bar.addMenu('&Help')
        help_menu.addAction(about_action)

        self.main_widget = MainWidget(self)
        self.setCentralWidget(self.main_widget)

        logger.debug("QMainWindow created")

    def new_vnc_session(self):
        last_tab_id = self.main_widget.tabs.count() - 1
        self.main_widget.tabs.setTabText(last_tab_id, "Login...")
        self.main_widget.add_new_tab("+")

    def open_vnc_session(self):

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileName(self,
                                                  "Open...",
                                                  "",
                                                  "VNC Files (*.vnc);;All Files (*)",
                                                  options=options)

    def exit(self):
        self.close()

    def edit_settings(self):
        return

    def about(self):
        return


class MainWidget(QWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)

        self.main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        self.init_ui()

    def init_ui(self):
        """
        Initialize the interface
        """

    # Initialize tab screen
        self.tabs.resize(300, 200)
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
        text_log_label.setText('Idle')
        text_log_label.setFrameShape(QFrame.Panel)
        text_log_label.setFrameShadow(QFrame.Sunken)
        text_log_label.setLineWidth(1)
        logger.debug("Added Log Label")
        text_log_handler = QLabelLoggerHandler(text_log_label)
        logger.addHandler(text_log_handler)
        logger.debug("Set the log handler")
        self.main_layout.addWidget(text_log_label)

    # Set main layout
        self.setLayout(self.main_layout)

    @pyqtSlot()
    def on_change(self):
        """
        Add a new "+" tab and substitute "+2" with "login" in the previous tab
        if the last tab is selected
        :return:
        """
        if self.tabs.currentIndex() == self.tabs.count() - 1:
            self.tabs.setTabText(self.tabs.currentIndex(), "Login...")
            self.add_new_tab("+")

    def add_new_tab(self, session_name):
        """
        Add a new tab in the tab widget
        :param session_name: name to be displayed
        :return:
        """
        new_tab = QSessionWidget(self.tabs)
        self.tabs.addTab(new_tab, session_name)
        new_tab.logged_in.connect(self.on_login)
        logger.debug("Added new tab: " + str(session_name))

    @pyqtSlot(str)
    def on_login(self, session_name):
        self.tabs.setTabText(self.tabs.currentIndex(), session_name)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    rcm_win = RCMMainWindow()
    rcm_win.show()
    sys.exit(app.exec_())
