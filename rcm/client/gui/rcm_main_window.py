# std lib
import collections

# pyqt5
from PyQt5.QtCore import pyqtSlot, QThreadPool, Qt
from PyQt5.QtGui import QIcon, QTextCursor
from PyQt5.QtWidgets import QMainWindow, QWidget, \
    QTabWidget, QVBoxLayout, QPushButton, \
    QDesktopWidget, QAction, QFileDialog, \
    QTabBar, QStyle, QPlainTextEdit, QMessageBox, QSplitter

# local includes
from client.gui.ssh_session_widget import QSSHSessionWidget
from client.gui.edit_settings_dialog import QEditSettingsDialog
from client.utils.pyinstaller_utils import resource_path
from client.log.logger import QTextEditLoggerHandler, logger, logic_logger
import server.rcm as rcm


class RCMMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        title = "Remote Connection Manager - CINECA - v0.01_alpha"
        self.setWindowTitle(title)

        width = 1000
        height = 370

        screen_width = QDesktopWidget().width()
        screen_height = QDesktopWidget().height()

        self.setGeometry((screen_width / 2) - (width / 2),
                         (screen_height / 2) - (height / 2),
                         width, height)

        self.setMinimumHeight(height)
        self.setMinimumWidth(width)

        self.build_menu()

        self.main_widget = MainWidget(self)
        self.setCentralWidget(self.main_widget)

        self.thread_pool = QThreadPool()

        logger.info("Welcome in RCM!")
        logger.debug("Multithreading with maximum %d threads" % self.thread_pool.maxThreadCount())

    def build_menu(self):
        """
        build and add menu to the application
        :return:
        """

        # Create new action
        new_action = QAction(QIcon(resource_path('gui/icons/new.png')), '&New', self)
        new_action.setShortcut('Ctrl+N')
        new_action.setStatusTip('New VNC session')
        new_action.triggered.connect(self.new_vnc_session)

        # Create new action
        open_action = QAction(QIcon(resource_path('gui/icons/open.png')), '&Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Open VNC session')
        open_action.triggered.connect(self.open_vnc_session)

        # Create exit action
        exit_action = QAction(QIcon(resource_path('gui/icons/exit.png')), '&Exit', self)
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

    def new_vnc_session(self):
        last_tab_id = self.main_widget.tabs.count() - 1
        last_tab_uuid = self.main_widget.tabs.widget(last_tab_id).uuid

        kill_btn = QPushButton()
        kill_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        kill_btn.clicked.connect(lambda: self.on_close(last_tab_uuid))
        kill_btn.setToolTip('Close session')

        self.main_widget.tabs.setTabText(last_tab_id, "Login...")
        self.main_widget.tabs.tabBar().setTabButton(last_tab_id,
                                                    QTabBar.RightSide,
                                                    kill_btn)
        self.main_widget.add_new_tab("", False)

    def open_vnc_session(self):

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileName(self,
                                                  "Open...",
                                                  "",
                                                  "VNC Files (*.vnc);;All Files (*)",
                                                  options=options)

        current_session_widget = self.main_widget.tabs.currentWidget()

        if filename:
            # check if session needs tunneling
            file = open(filename, 'r')
            if 'rcm_tunnel' in file.read():
                file.seek(0)
                lines = file.readlines()
                for line in lines:
                    if 'rcm_tunnel' in line:
                        node = line.split('=')[1].rstrip()
                        if not current_session_widget.is_logged:
                            logger.error("You are not logged in the current session. Please log in.")
                            return
                        if node == current_session_widget.host:
                            user = current_session_widget.user
                        else:
                            logger.error("The host of the current session (" +
                                         current_session_widget.host +
                                         ") is different from the host of the vnc file (" +
                                         node + ")")
                            return
                    if 'host' in line:
                        hostname = line.split('=')[1].rstrip()
                    if 'port' in line:
                        port = line.split('=')[1].rstrip()
                        display = int(port) - 5900
                    if 'password' in line:
                        password = line.split('=')[1].rstrip()

                session = rcm.rcm_session(node=hostname,
                                          tunnel='y',
                                          display=display,
                                          nodelogin=node,
                                          username=user,
                                          vncpassword=password)
                current_session_widget.remote_connection_manager.vncsession(session=session)
                logger.info("Connected to remote display " +
                            str(display) + " on " + node +
                            " as " + str(user) + " with tunnel")
            else:
                current_session_widget.remote_connection_manager.vncsession(configFile=filename)

    def exit(self):
        self.close()

    def edit_settings(self):
        edit_settings_dlg = QEditSettingsDialog(self)
        edit_settings_dlg.setModal(True)
        edit_settings_dlg.exec()

    def about(self):
        QMessageBox.about(self, "RCM", self.windowTitle())
        return

    @pyqtSlot()
    def on_close(self, uuid):
        # loop over the tabs and found the tab with the right uuid
        for tab_id in range(0, self.main_widget.tabs.count()):
            widget = self.main_widget.tabs.widget(tab_id)
            if widget.uuid == uuid:
                if self.main_widget.tabs.currentIndex() == self.main_widget.tabs.count() - 2:
                    self.main_widget.tabs.setCurrentIndex(tab_id - 1)
                self.main_widget.tabs.removeTab(tab_id)
                return


class MainWidget(QWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)

        self.main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget(self)
        self.text_log_frame = None

        self.init_ui()

    def init_ui(self):
        """
        Initialize the interface
        """

        # layout the tab and textedit widgets inside the splitter
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)

        # Add tabs
        self.add_new_tab("Login...")
        self.add_new_tab("", False)
        self.tabs.currentChanged.connect(self.on_change)
        splitter.addWidget(self.tabs)

        # Add text log
        self.text_log_frame = QPlainTextEdit(self)
        splitter.addWidget(self.text_log_frame)

        # configure logging
        text_log_handler = QTextEditLoggerHandler(self.text_log_frame)
        text_log_handler.logger_signals.log_message.connect(self.on_log)
        logger.addHandler(text_log_handler)
        logic_logger.addHandler(text_log_handler)

        # add the splitter to the main layout
        self.main_layout.addWidget(splitter)

        # Set main layout
        self.setLayout(self.main_layout)

    @pyqtSlot(str)
    def on_log(self, html_msg):
        self.text_log_frame.moveCursor(QTextCursor.EndOfLine)
        self.text_log_frame.appendHtml(html_msg)

    @pyqtSlot()
    def on_change(self):
        """
        Add a new "+" tab and substitute "+" with "login" in the previous tab
        if the last tab is selected
        :return:
        """
        if self.tabs.currentIndex() == self.tabs.count() - 1:
            self.tabs.setTabText(self.tabs.currentIndex(), "Login...")

            uuid = self.tabs.currentWidget().uuid

            kill_btn = QPushButton()
            kill_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
            kill_btn.setToolTip('Close session')
            kill_btn.clicked.connect(lambda: self.on_close(uuid))
            self.tabs.tabBar().setTabButton(self.tabs.currentIndex(),
                                            QTabBar.RightSide,
                                            kill_btn)
            self.add_new_tab("", False)

    @pyqtSlot()
    def on_new(self):
        """
        Add a new "+" tab and substitute "+" with "login" in the previous tab
        if the last tab button is pressed
        :return:
        """
        last_tab = self.tabs.count() - 1
        self.tabs.setTabText(last_tab, "Login...")

        kill_btn = QPushButton()
        kill_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        kill_btn.setToolTip('Close session')
        uuid = self.tabs.widget(last_tab).uuid
        kill_btn.clicked.connect(lambda: self.on_close(uuid))
        self.tabs.tabBar().setTabButton(last_tab,
                                        QTabBar.RightSide,
                                        kill_btn)
        self.add_new_tab("", False)

    def add_new_tab(self, session_name, show_close_btn=True):
        """
        Add a new tab in the tab widget
        :param session_name: name to be displayed
        :param show_close_btn: if true we add the close button
        :return:
        """
        new_tab = QSSHSessionWidget(self)
        uuid = new_tab.uuid
        self.tabs.addTab(new_tab, session_name)

        if show_close_btn:
            kill_btn = QPushButton()
            kill_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
            kill_btn.clicked.connect(lambda: self.on_close(uuid))
            kill_btn.setToolTip('Close session')
            self.tabs.tabBar().setTabButton(self.tabs.count() - 1,
                                            QTabBar.RightSide,
                                            kill_btn)
        else:
            kill_btn = QPushButton()
            ico = QIcon()
            ico.addFile(resource_path('gui/icons/plus.png'))
            kill_btn.setIcon(ico)
            kill_btn.clicked.connect(self.on_new)
            kill_btn.setToolTip('New session')
            self.tabs.tabBar().setTabButton(self.tabs.count() - 1,
                                            QTabBar.RightSide,
                                            kill_btn)

        new_tab.logged_in.connect(self.on_login)
        new_tab.sessions_changed.connect(self.on_sessions_changed)
        logger.debug("Added new tab " + str(uuid))

    @pyqtSlot(str)
    def on_login(self, session_name):
        self.tabs.setTabText(self.tabs.currentIndex(), session_name)

    @pyqtSlot()
    def on_close(self, uuid):
        # loop over the tabs and found the tab with the right uuid
        for tab_id in range(0, self.tabs.count()):
            widget = self.tabs.widget(tab_id)
            if widget.uuid == uuid:
                if self.tabs.currentIndex() == self.tabs.count() - 2:
                    self.tabs.setCurrentIndex(tab_id - 1)
                # kill all the pending threads
                if widget.remote_connection_manager:
                    widget.remote_connection_manager.vncsession_kill()
                widget.kill_all_threads()
                self.tabs.removeTab(tab_id)
                widget.setParent(None)
                return

    @pyqtSlot(collections.deque)
    def on_sessions_changed(self, sessions_list):
        for tab_id in range(0, self.tabs.count()):
            widget = self.tabs.widget(tab_id)
            widget.session_combo.clear()
            widget.session_combo.addItems(sessions_list)
            widget.session_combo.activated.emit(0)
