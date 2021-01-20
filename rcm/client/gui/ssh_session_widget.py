#
# Copyright (c) 2014-2019 CINECA.
#
# This file is part of RCM (Remote Connection Manager) 
# (see http://www.hpc.cineca.it/software/rcm).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import json
import uuid
import os.path
import collections
import sys
import time
import tempfile
import subprocess
import hashlib


# pyqt5
from PyQt5.QtCore import QSize, pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, \
    QGridLayout, QVBoxLayout, QLineEdit, QHBoxLayout, QPushButton, \
    QStyle, QProgressBar, QMessageBox, QInputDialog

# local includes
from client.gui.display_dialog import QDisplayDialog
from client.gui.dynamic_display_dialog import QDynamicDisplayDialog
from client.gui.display_session_widget import QDisplaySessionWidget
from client.utils.pyinstaller_utils import resource_path
from client.miscellaneous.logger import logger
from client.miscellaneous.config_parser import parser, config_file_name, preset_sessions, merge_preset_sessions
from client.logic import manager
from client.gui.thread import LoginThread, ReloadThread
from client.gui.worker import Worker
from client.utils.rcm_enum import Status
import client.logic.rcm_utils as rcm_utils
import client.logic.plugin as plugin
import client.utils.pyinstaller_utils as pyinstaller_utils


class QSSHSessionWidget(QWidget):
    """
    Create a new ssh session widget to be put inside a tab in the main window
    For each ssh session we can have many display sessions
    """

    # define a signal when the user successful log in
    logged_in = pyqtSignal(str, str)
    prompt_response_signal=pyqtSignal(str)

    sessions_changed = pyqtSignal(collections.deque, collections.deque)

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)

        self.user = ""
        self.host = ""
        self.session_name = ""
        self.display_sessions = None
        self.displays = {}
        self.sessions_list = collections.deque(maxlen=5)
        self.platform_config = None
        self.remote_connection_manager = None
        self.is_logged = False

        # threads
        self.login_thread = None
        self.reload_thread = None

        # widgets
        self.session_combo = QComboBox(self)
        self.host_line = QLineEdit(self)
        self.user_line = QLineEdit(self)
        self.pssw_line = QLineEdit(self)
        self.preload_line = QLineEdit(self)
        self.login_button = None

        # containers
        self.containerLoginWidget = QWidget()
        self.containerSessionWidget = QWidget()
        self.containerWaitingWidget = QWidget()
        self.containerReloadWidget = QWidget()

        # layouts
        self.session_ver_layout = QVBoxLayout()
        self.rows_ver_layout = QVBoxLayout()

        self.init_ui()

        self.uuid = uuid.uuid4().hex

        self.prompt_response=None
        self.prompt_response_signal.connect(self.set_prompt_response)

    def set_prompt_response(self,text):
        self.prompt_response = text

    def init_ui(self):
        """
        Initialize the interface
        """

    # Login Layout
    # grid login layout
        grid_login_layout = QGridLayout()

        try:
            sessions_list = parser.get('LoginFields', 'hostList', fallback=preset_sessions)
            user_sessions = json.loads(sessions_list)
            self.sessions_list = collections.deque(merge_preset_sessions(user_sessions, json.loads(preset_sessions)), maxlen=20)
        except Exception:
            self.sessions_list = collections.deque(json.loads(preset_sessions), maxlen=20)

        session_label = QLabel(self)
        session_label.setText('Sessions:')
        self.session_combo.clear()
        self.session_combo.addItems(self.sessions_list_names())

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
        grid_login_layout.addWidget(self.user_line, 2, 1)

        pssw_label = QLabel(self)
        pssw_label.setText('Password:')
        self.pssw_line.setEchoMode(QLineEdit.Password)
        grid_login_layout.addWidget(pssw_label, 3, 0)
        grid_login_layout.addWidget(self.pssw_line, 3, 1)

        preload_label = QLabel(self)
        preload_label.setText('Preload:')
        grid_login_layout.addWidget(preload_label, 4, 0)
        grid_login_layout.addWidget(self.preload_line, 4, 1)

        # hor login layout
        self.login_button = QPushButton('Login', self)
        self.login_button.clicked.connect(self.login)
        self.login_button.setShortcut("Return")

        login_hor_layout = QHBoxLayout()
        login_hor_layout.addStretch(1)
        login_hor_layout.addWidget(self.login_button)
        login_hor_layout.addStretch(1)

    # container login widget
        # it disappears when the user logged in
        login_layout = QVBoxLayout()
        login_layout.addStretch(1)
        login_layout.addLayout(grid_login_layout)
        login_layout.addLayout(login_hor_layout)
        login_layout.addStretch(1)

        self.containerLoginWidget.setLayout(login_layout)

    # Create the main layout
        new_tab_main_layout = QVBoxLayout()
        new_tab_main_layout.addWidget(self.containerLoginWidget)

    # container waiting widget
        ver_waiting_layout = QVBoxLayout()

        first_hor_waiting_layout = QHBoxLayout()
        second_hor_waiting_layout = QHBoxLayout()
        third_hor_waiting_layout = QHBoxLayout()

        connecting_label = QLabel(self)
        connecting_label.setText("Connecting...")

        first_hor_waiting_layout.addStretch(0)
        first_hor_waiting_layout.addWidget(connecting_label)
        first_hor_waiting_layout.addStretch(0)

        prog_bar = QProgressBar(self)
        prog_bar.setMinimum(0)
        prog_bar.setMaximum(0)
        prog_bar.setAlignment(Qt.AlignCenter)

        second_hor_waiting_layout.addStretch(0)
        second_hor_waiting_layout.addWidget(prog_bar)
        second_hor_waiting_layout.addStretch(0)

        waiting_kill_btn = QPushButton(self)
        waiting_kill_btn.setText('Cancel')
        waiting_kill_btn.setToolTip('Kill the ssh login process')
        waiting_kill_btn.clicked.connect(self.kill_login_thread)

        third_hor_waiting_layout.addStretch(0)
        third_hor_waiting_layout.addWidget(waiting_kill_btn)
        third_hor_waiting_layout.addStretch(0)

        ver_waiting_layout.addStretch(0)
        ver_waiting_layout.addLayout(first_hor_waiting_layout)
        ver_waiting_layout.addLayout(second_hor_waiting_layout)
        ver_waiting_layout.addLayout(third_hor_waiting_layout)
        ver_waiting_layout.addStretch(0)

        self.containerWaitingWidget.setLayout(ver_waiting_layout)
        new_tab_main_layout.addWidget(self.containerWaitingWidget)
        self.containerWaitingWidget.hide()

    # reload waiting widget
        ver_reload_layout = QVBoxLayout()

        first_hor_reload_layout = QHBoxLayout()
        second_hor_reload_layout = QHBoxLayout()
        third_hor_reload_layout = QHBoxLayout()

        reload_label = QLabel(self)
        reload_label.setText("Reloading...")

        first_hor_reload_layout.addStretch(0)
        first_hor_reload_layout.addWidget(reload_label)
        first_hor_reload_layout.addStretch(0)

        reload_prog_bar = QProgressBar(self)
        reload_prog_bar.setMinimum(0)
        reload_prog_bar.setMaximum(0)
        reload_prog_bar.setAlignment(Qt.AlignCenter)

        second_hor_reload_layout.addStretch(0)
        second_hor_reload_layout.addWidget(reload_prog_bar)
        second_hor_reload_layout.addStretch(0)

        reload_btn = QPushButton(self)
        reload_btn.setText('Cancel')
        reload_btn.setToolTip('Kill the reload process')
        reload_btn.clicked.connect(self.kill_reload_thread)

        third_hor_reload_layout.addStretch(0)
        third_hor_reload_layout.addWidget(reload_btn)
        third_hor_reload_layout.addStretch(0)

        ver_reload_layout.addStretch(0)
        ver_reload_layout.addLayout(first_hor_reload_layout)
        ver_reload_layout.addLayout(second_hor_reload_layout)
        ver_reload_layout.addLayout(third_hor_reload_layout)
        ver_reload_layout.addStretch(0)

        self.containerReloadWidget.setLayout(ver_reload_layout)
        new_tab_main_layout.addWidget(self.containerReloadWidget)
        self.containerReloadWidget.hide()

    # container session widget
        plusbutton_layout = QHBoxLayout()
        plusbutton_layout.setContentsMargins(0, 0, 0, 0)
        plusbutton_layout.setSpacing(0)

        self.session_ver_layout.addLayout(plusbutton_layout)
        self.session_ver_layout.addLayout(self.rows_ver_layout)
        self.session_ver_layout.addStretch(1)

        font = QFont()
        font.setBold(True)

        name = QLabel()
        name.setText("Name")
        name.setMinimumWidth(300)
        name.setFont(font)
        plusbutton_layout.addWidget(name)

        status = QLabel()
        status.setText("Status")
        status.setMinimumWidth(40)
        status.setFont(font)
        plusbutton_layout.addWidget(status)

        time = QLabel()
        time.setText("Time")
        time.setMinimumWidth(40)
        time.setFont(font)
        plusbutton_layout.addWidget(time)

        resources = QLabel()
        resources.setText("Resources")
        resources.setMinimumWidth(40)
        resources.setFont(font)
        plusbutton_layout.addWidget(resources)

        separator_label = QLabel()
        separator_label.setText("")
        plusbutton_layout.addWidget(separator_label)
        plusbutton_layout.addWidget(separator_label)

        self.new_display_ico = QIcon()
        self.new_display_ico.addFile(resource_path('gui/icons/plus.png'), QSize(16, 16))

        self.new_display_btn = QPushButton()
        self.new_display_btn.setIcon(self.new_display_ico)
        self.new_display_btn.setToolTip('Create a new display session')
        self.new_display_btn.clicked.connect(self.add_new_display)
        self.new_display_btn.setShortcut(Qt.Key_Plus)

        reload_btn = QPushButton()
        reload_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        reload_btn.setToolTip('Reload the page')
        reload_btn.clicked.connect(self.reload)
        reload_btn.setShortcut("F5")

        self.new_display_layout = QHBoxLayout()
        self.new_display_layout.addWidget(reload_btn)
        self.new_display_layout.addWidget(self.new_display_btn)

        plusbutton_layout.addLayout(self.new_display_layout)

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
            curr_session = self.session_find(self.session_combo.currentText())
            if curr_session:
                self.session_name, self.host, self.user, self.preload = self.session_find(self.session_combo.currentText())
            else:
                self.user, self.host = (self.session_combo.currentText().split('@')[0], self.session_combo.currentText().split('@')[1].split('?')[0])
                self.preload=''
            self.user_line.setText(self.user)
            self.host_line.setText(self.host)
            self.preload_line.setText(self.preload)
        except ValueError:
            pass

#unused    def create_remote_connection_manager(self):
#unused        if not self.remote_connection_manager:
#unused            self.remote_connection_manager = manager.RemoteConnectionManager()

    def login(self):
        if self.user != str(self.user_line.text()):
            self.user = str(self.user_line.text())
            self.session_name = ''
        if self.host != str(self.host_line.text()):
            self.host = str(self.host_line.text())
            self.session_name = ''
        if self.preload != str(self.preload_line.text()):
            self.preload = str(self.preload_line.text())
            self.session_name = ''
        password = str(self.pssw_line.text())

        if not self.host:
            logger.warning("Host field is empty")
            return

        if not self.user:
            logger.warning("User field is empty")
            return

        if not self.session_name:
            self.session_name = self.user + "@" + self.host
            if self.preload:
                # search this preload into existing sessions
                preload_name = ''
                for session_name,host,user,preload in self.sessions_list:
                    if preload == self.preload:
                        preload_name = ([''] + session_name.split('?')[1:])[-1]
                        break
                if not preload_name:
                    preload_name = hashlib.md5(self.preload.encode()).hexdigest()[:4]
                self.session_name += "?" + preload_name
        logger.info("Logging...")

        # Show the waiting widget
        self.containerLoginWidget.hide()
        self.containerSessionWidget.hide()
        self.containerWaitingWidget.show()

        self.plugin_registry = plugin.PluginRegistry()
        ssh_command_prompt_handlers=[('First Factor:',self.login_popup_dialog), ('Second Factor:',self.login_popup_dialog), ('password:',self.login_popup_dialog)]
        self.plugin_registry.register_plugins_params('CommandExecutor',{'prompt_handlers': ssh_command_prompt_handlers})
        self.remote_connection_manager = manager.RemoteConnectionManager(plugin_registry=self.plugin_registry)
        self.remote_connection_manager.debug = False

        self.login_thread = LoginThread(self, self.host, self.user, password, preload=self.preload)
        self.login_thread.finished.connect(self.on_logged)
        self.login_thread.prompt.connect(self.real_popup_dialog)

        self.login_thread.start()

    def real_popup_dialog(self,title_text):
        text, ok = QInputDialog.getText(self, title_text, 'Ok')
        self.prompt_response_signal.emit(text)

    def login_popup_dialog(self,title_text='',ok_text='Ok'):
        print("prompt is -->" + title_text)
        self.prompt_response=None
        self.login_thread.prompt.emit(title_text)
        #text, ok = QInputDialog.getText(self, title_text, ok_text)
        #line = input()
        while None == self.prompt_response:
            time.sleep(1)
        print("received -->" + self.prompt_response + "<--")
        #text=line.strip()
        ok=True
        return ( self.prompt_response, ok)


    def on_logged(self):
        if self.is_logged:
            # Show the session widget
            self.containerLoginWidget.hide()
            self.containerWaitingWidget.hide()
            self.containerSessionWidget.show()

            logger.info("Logged as " + self.user + " to " + self.host)

            # update sessions list
            # warning, json load turns tuple into list
            # append new session only if content is different
            if self.session_name and list(self.session_tuple())[1:] not in list(self.sessions_list_content()):
                self.sessions_list.appendleft(self.session_tuple())
                #self.sessions_changed.emit(self.sessions_list)
                self.sessions_changed.emit(self.sessions_list_names(), self.sessions_list)

            # update config file
            self.update_config_file(self.session_name)

            # check if a new version is available
            self.update_executable()

            # Emit the logged_in signal.
            self.logged_in.emit(self.session_name, self.uuid)

            # update the session list to be shown
            self.reload()
        else:
            # Show the login widget again
            self.containerLoginWidget.show()
            self.containerSessionWidget.hide()
            self.containerWaitingWidget.hide()

    def update_executable(self):
        # update the executable only if we are running in a bundle
        if not pyinstaller_utils.is_bundled():
            return

        logger.info("Checking if a new client version is available...")
        current_exe_checksum = rcm_utils.compute_checksum(sys.executable)
        logger.debug("Current client checksum: " + str(current_exe_checksum))

        last_exe_checksum, last_exe_url = self.platform_config.get_version()

        if not last_exe_checksum :
            logger.debug("Missing platform exe update checksum , url: " + str(last_exe_url))
            last_exe_checksum = current_exe_checksum
        else :
            if not last_exe_url :
                logger.debug("Missing platform exe update url for checksum: "+ str(last_exe_checksum))
                last_exe_checksum = current_exe_checksum
        logger.debug("New client checksum: " + str(last_exe_checksum))

        if current_exe_checksum != last_exe_checksum:
            question_title = "Release download"
            question_text = "A new version of the \"Remote Connection Manager\" is available at: " \
                            + last_exe_url + ". " \
                            "It is highly recommended to install the new version to keep working properly. " \
                            "Do you want to install it now?"

            buttonReply = QMessageBox.question(self, question_title, question_text,
                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if buttonReply == QMessageBox.No:
                return

            logger.info('Downloading the new client version...')
            exe_dir = os.path.dirname(sys.executable)
            tmp_dir = tempfile.gettempdir()
            last_exe_path = os.path.join(tmp_dir, os.path.basename(sys.executable))
            rcm_utils.download_file(last_exe_url, last_exe_path)
            downloaded_exe_checksum = rcm_utils.compute_checksum(last_exe_path)
            time.sleep(5)

            if downloaded_exe_checksum != last_exe_checksum:
                logger.warning('Downloaded file checksum mismatched. '
                               'Expected: ' + str(last_exe_path) + '. Found: '
                               + str(downloaded_exe_checksum) + '. Update stopped.')
                os.remove(last_exe_path)
            else:
                if sys.platform == 'win32':
                    batch_filename = os.path.join(tmp_dir, "RCM_update.bat")
                    with open(batch_filename, 'w') as batch_file:
                        batch_file.write("rem start update bat" + "\n")
                        batch_file.write("cd /D " + exe_dir + "\n")
                        batch_file.write("copy mybatch.bat mybatch.txt\n")
                        batch_file.write('ping -n 3 localhost >nul 2>&1' + "\n")
                        batch_file.write("del mybatch.txt\n")
                        batch_file.write("ren " + os.path.basename(sys.executable) +
                                         " _" + os.path.basename(sys.executable) + "\n")
                        batch_file.write("copy " + last_exe_path + "\n")
                        batch_file.write("del " + " _" + os.path.basename(sys.executable) + "\n")
                        batch_file.write("del " + last_exe_path + "\n")
                        batch_file.write("start " + os.path.basename(sys.executable) + "\n")
                        batch_file.write("del " + batch_filename + "\n")
                        batch_file.write("exit\n")

                    logger.info("The application will be closed and the new one will start in a while.")
                    os.startfile(batch_filename)
                else:
                    batch_filename = os.path.join(tmp_dir, "RCM_update.sh")
                    with open(batch_filename, 'w') as batch_file:
                        batch_file.write("#!/bin/bash\n")
                        batch_file.write("#start update bat" + "\n")
                        batch_file.write("cd " + exe_dir + "\n")
                        batch_file.write("sleep 3 \n")
                        batch_file.write("rm " + os.path.basename(sys.executable) + "\n")
                        batch_file.write("cp " + last_exe_path + " .\n")
                        batch_file.write("chmod a+x " + os.path.basename(sys.executable) + "\n")
                        batch_file.write("sleep 2 \n")
                        batch_file.write("./" + os.path.basename(sys.executable) + "\n")

                    logger.info("The application will be closed and the new one will start in a while!")
                    subprocess.Popen(["sh", batch_filename])
        else:
            logger.info('The client is up-to-date')

    def add_new_display(self):
        # cannot have more than 5 sessions
        if len(self.displays) >= 5:
            logger.warning("You have already 5 displays")
            return

        display_dialog_ui = None
        if self.platform_config:
            if 'jobscript_json_menu' in self.platform_config.config:
                display_dialog_ui = json.loads(self.platform_config.config.get('jobscript_json_menu', '{}'),
                                               object_pairs_hook=collections.OrderedDict)
        if display_dialog_ui:
            display_dlg = QDynamicDisplayDialog(display_dialog_ui)
        else:
            display_dlg = QDisplayDialog(list(self.displays.keys()),
                                         self.platform_config)
        display_dlg.setModal(True)

        if display_dlg.exec() != 1:
            return

        display_name = display_dlg.display_name
        display_id = '-'.join((display_name, str(uuid.uuid4())))
        display_widget = QDisplaySessionWidget(self,
                                               display_id=display_id,
                                               display_name=display_name)
        self.rows_ver_layout.addWidget(display_widget)
        self.displays[display_id] = display_widget

        # start the worker
        worker = Worker(display_widget,
                        self.remote_connection_manager,
                        display_dlg)
        worker.signals.status.connect(display_widget.on_status_change)
        self.window().thread_pool.start(worker)

        logger.info("Added new display")


    def update_config_file(self, session_name):
        """
        Update the config file with the new session name
        :param session_name: name of the last session inserted by the user
        :return:
        """
        if not parser.has_section('LoginFields'):
            parser.add_section('LoginFields')

        parser.set('LoginFields', 'hostList', json.dumps(list(self.sessions_list), indent=4))

        try:
            config_file_dir = os.path.dirname(config_file_name)
            if not os.path.exists(config_file_dir):
                os.makedirs(config_file_dir)

            with open(config_file_name, 'w') as config_file:
                parser.write(config_file)
        except:
            logger.error("failed to dump the session list in the configuration file")

    def remove_display(self, id):
        """
        Remove the display widget from the tab
        :param id: display id name
        :return:
        """
        # first we hide the display
        logger.debug("Hiding display " + str(id))
        self.displays[id].hide()

        # then we remove it from the layout and from the dictionary
        self.rows_ver_layout.removeWidget(self.displays[id])
        self.displays[id].setParent(None)
        del self.displays[id]

        logger.info("Removed display " + str(id))

    def reload(self):
        logger.debug("Reloading...")

        # Show the reload widget
        self.containerLoginWidget.hide()
        self.containerSessionWidget.hide()
        self.containerWaitingWidget.hide()
        self.containerReloadWidget.show()

        self.reload_thread = ReloadThread(self)
        self.reload_thread.finished.connect(self.on_reloaded)
        self.reload_thread.start()

    def on_reloaded(self):
        if self.display_sessions:
            # kill not existing sessions
            for display_id in list(self.displays.keys()):
                missing = True
                for session in self.display_sessions.get_sessions():
                    if str(display_id) == str(session.hash['session name']):
                        missing = False
                        break
                if missing:
                    self.remove_display(display_id)

            # update or create from scratch new sessions
            for session in self.display_sessions.get_sessions():
                display_id = str(session.hash['session name'])
                display_state = str(session.hash['state'])
                display_node = str(session.hash['node'])
                display_name = display_id.split('-')[0]
                display_timeleft = str(session.hash['timeleft'])

                if display_id in self.displays.keys():
                    logger.debug("Display " + display_id + " already exists")
                    self.displays[display_id].session = session
                    if self.displays[display_id].status != Status(display_state):
                        self.displays[display_id].status = Status(display_state)
                        self.displays[display_id].update_gui()
                else:
                    display_widget = QDisplaySessionWidget(parent=self,
                                                           display_id=display_id,
                                                           display_name=display_name,
                                                           session=session,
                                                           status=Status(display_state),
                                                           resources=display_node,
                                                           timeleft=display_timeleft)
                    self.rows_ver_layout.addWidget(display_widget)
                    self.displays[display_id] = display_widget
                    logger.debug("Created display " + display_id)

        # Show the reload widget
        self.containerLoginWidget.hide()
        self.containerSessionWidget.show()
        self.containerWaitingWidget.hide()
        self.containerReloadWidget.hide()

    def kill_all_threads(self):
        try:
            self.kill_login_thread()
            self.kill_reload_thread()

            for display_session_id in self.displays.keys():
                self.displays[display_session_id].kill_all_threads()

            if self.remote_connection_manager:
                self.remote_connection_manager.kill_session_thread()
        except Exception as e:
            logger.error('Failed to kill running threads')
            logger.error(e)

    def kill_login_thread(self):
        if self.login_thread:
            if not self.login_thread.isFinished():
                logger.debug("killing login thread")
                self.login_thread.terminate()

    def kill_reload_thread(self):
        if self.reload_thread:
            if not self.reload_thread.isFinished():
                logger.debug("killing reload thread")
                self.reload_thread.terminate()

    def sessions_list_names(self):

        sessions_list_name=collections.deque()
        for sess_name in self.sessions_list:
            sessions_list_name.append(sess_name[0])
        return sessions_list_name

    def sessions_list_content(self):

        sessions_list_content=collections.deque()
        for sess_name in self.sessions_list:
            sessions_list_content.append(sess_name[1:])
        return sessions_list_content

    def session_tuple(self):
        return (self.session_name, self.host, self.user, self.preload)

    def session_find(self,session_name):
        found=None
        for session in self.sessions_list:
            if session[0] == session_name:
                found=session
                break
        return found