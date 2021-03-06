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

from datetime import timedelta, datetime
import time
import traceback

# pyqt5
from PyQt5.QtCore import pyqtSignal, QTimer, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QFrame, QLabel, \
    QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog

# local includes
from client.utils.pyinstaller_utils import resource_path
from client.miscellaneous.logger import logger
from client.gui.thread import KillThread
from client.utils.rcm_enum import Status


class QDisplaySessionWidget(QWidget):
    """
    Create a new row (display session widget) to be put inside
    the table shown in the ssh session widget
    """

    terminate = pyqtSignal(str)

    def __init__(self,
                 parent,
                 display_id,
                 display_name,
                 session=None,
                 status=Status.NOTDEFINED,
                 resources="Not defined",
                 timeleft=None):
        super().__init__(parent)

        self.parent = parent
        self.session = session
        self.display_id = display_id
        self.display_name = display_name
        self.status = status
        self.resources = resources

        if timeleft is not None:
            try:
                strp_time = datetime.strptime(timeleft, "%H:%M:%S")
                self.timeleft = timedelta(hours=strp_time.hour,
                                          minutes=strp_time.minute,
                                          seconds=strp_time.second)
            except:
                self.timeleft=None
        else:
            self.timeleft = timeleft

        # icons
        self.connect_ico = QIcon()
        self.kill_ico = QIcon()
        self.share_ico = QIcon()

        # threads
        self.kill_thread = None

        self.init_ui()

    def init_ui(self):
        """
        Initialize the interface
        """

        self.connect_ico.addFile(resource_path('gui/icons/connect.png'))
        self.kill_ico.addFile(resource_path('gui/icons/kill.png'))
        self.share_ico.addFile(resource_path('gui/icons/share.png'))

        display_hor_layout = QHBoxLayout()
        display_hor_layout.setContentsMargins(0, 0, 0, 0)
        display_hor_layout.setSpacing(0)

        display_ver_layout = QVBoxLayout()
        display_ver_layout.setContentsMargins(0, 0, 0, 0)
        display_ver_layout.setSpacing(0)

        display_ver_layout.addLayout(display_hor_layout)

        self.setLayout(display_ver_layout)

        name = QLabel(self)
        name.setMinimumWidth(300)
        name.setText(str(self.display_name)[:40])
        display_hor_layout.addWidget(name)

        self.status_label = QLabel(self)
        self.status_label.setText(str(self.status))
        self.status_label.setMinimumWidth(40)
        display_hor_layout.addWidget(self.status_label)

        self.time = QLabel(self)
        self.time.setMinimumWidth(40)
        if self.timeleft is not None:
            self.time.setText(str(self.timeleft))
        else:
            self.time.setText("Not defined")
        display_hor_layout.addWidget(self.time)

        timer = QTimer(self)
        timer.timeout.connect(self.time_update)
        timer.start(1000)

        self.resources_label = QLabel(self)
        self.resources_label.setMinimumWidth(40)
        self.resources_label.setText(self.resources)
        display_hor_layout.addWidget(self.resources_label)

        self.connect_btn = QPushButton(self)
        self.connect_btn.setIcon(self.connect_ico)
        self.connect_btn.setToolTip('Connect to the remote display')
        self.connect_btn.clicked.connect(self.connect_display)
        display_hor_layout.addWidget(self.connect_btn)

        self.share_btn = QPushButton(self)
        self.share_btn.setIcon(self.share_ico)
        self.share_btn.setToolTip('Share the remote display via file')
        self.share_btn.clicked.connect(self.share_display)
        display_hor_layout.addWidget(self.share_btn)

        self.kill_btn = QPushButton(self)
        self.kill_btn.setIcon(self.kill_ico)
        self.kill_btn.setToolTip('Kill the remote display')
        self.kill_btn.clicked.connect(self.kill_display)
        self.terminate.connect(self.parentWidget().remove_display)

        display_hor_layout.addWidget(self.kill_btn)

        separator = QFrame(self)
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        display_ver_layout.addWidget(separator)

        self.update_gui()

    def connect_display(self):
        try:
            logger.info("Connecting to remote display " + str(self.display_name))
            self.parent.remote_connection_manager.submit(self.session,
                                                         gui_cmd=self.enable_connect_button)
        except:
            logger.error("Failed to connect to remote display " + str(self.display_name))

    def share_display(self):
        try:
            logger.info("Sharing display " + str(self.display_name))

            filename_suggested = self.session.hash['session name'].replace(' ', '_') + '.vnc'
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            filename, _ = QFileDialog.getSaveFileName(self,
                                                      "Share display " + str(self.display_name),
                                                      filename_suggested,
                                                      " Vnc Files (*.vnc);;All Files (*)",
                                                      options=options)

            if filename:
                with open(filename, 'w') as out_file:
                    out_file.write("[Connection]\n")
                    if self.session.hash['tunnel'] == 'y':
                        # rcm_tunnel is a key word to know that I need to tunnel across that node
                        out_file.write("rcm_tunnel={0}\n".format(self.session.hash['nodelogin']))
                        out_file.write("host={0}\n".format(self.session.hash['node']))
                    else:
                        out_file.write("host={0}\n".format(self.session.hash['nodelogin']))
                    try:
                        port = int(self.session.hash['port'])
                    except Exception as e:
                        logger.debug(str(e) + " - " + str(traceback.format_exc()))
                        port = 5900 + int(self.session.hash['display'])
                    out_file.write("port={0}\n".format( port ))
                    out_file.write("password={0}\n".format(self.session.hash['vncpassword']))
        except Exception as e:
            logger.debug(str(e) + " - " + str(traceback.format_exc()))
            logger.debug(str(self.session.hash))
            logger.error("Failed to share display " + str(self.display_name))

    def kill_display(self):
        """
        Kill the display running on the server
        :return:
        """
        current_status = self.status

        if self.status is Status.FINISHED:
            self.terminate.emit(self.display_id)
            return

        try:
            logger.debug("Killing remote display " + str(self.display_name))
            self.status = Status.KILLING
            self.update_gui()

            self.kill_thread = KillThread(self.parent,
                                          self.session,
                                          self,
                                          current_status)
            self.kill_thread.finished.connect(self.on_killed)
            self.kill_thread.start()
        except:
            logger.error("Failed to start kill remote display thread " + str(self.display_name))
            self.status = current_status
            self.update_gui()

    def on_killed(self):
        self.update_gui()
        if self.status is Status.FINISHED:
            self.terminate.emit(self.display_id)

    def time_update(self):
        """
        Update the time left of the job running on the server in the gui
        :return:
        """
        if self.status is Status.RUNNING:
            if self.timeleft:
                self.timeleft = self.timeleft - timedelta(seconds=1)
                self.time.setText(str(self.timeleft))
                self.time.update()

                x = time.strptime(str(self.timeleft).split(',')[0], '%H:%M:%S')
                num_seconds = int(timedelta(hours=x.tm_hour,
                                            minutes=x.tm_min,
                                            seconds=x.tm_sec).total_seconds())
                if num_seconds == 0:
                    self.status = Status.FINISHED
                    self.kill_display()

    def enable_connect_button(self, active):
        if active:
            self.connect_btn.setEnabled(False)
        else:
            self.connect_btn.setEnabled(True)

    @pyqtSlot(Status)
    def on_status_change(self, status):
        self.status = status
        self.update_gui()

    def update_gui(self):
        """
        Update the status of the job running on the server in the gui
        and set the buttons enabled True/False accordingly
        :return:
        """
        logger.debug("Updating display widget with status " + str(self.status))

        if self.status is Status.NOTDEFINED:
            self.connect_btn.setEnabled(False)
            self.share_btn.setEnabled(False)
            self.kill_btn.setEnabled(True)
            self.time.setText('Not defined')
            self.resources_label.setText('Not defined')

        if self.status is Status.PENDING:
            self.connect_btn.setEnabled(False)
            self.share_btn.setEnabled(False)
            self.kill_btn.setEnabled(True)
            self.time.setText('Not defined')
            self.resources_label.setText('Not defined')

        if self.status is Status.RUNNING:
            self.connect_btn.setEnabled(True)
            self.share_btn.setEnabled(True)
            self.kill_btn.setEnabled(True)
            if self.session:
                timeleft = str(self.session.hash['timeleft'])
                self.time.setText(timeleft)

                try:
                    strp_time = datetime.strptime(timeleft, "%H:%M:%S")
                    self.timeleft = timedelta(hours=strp_time.hour,
                                          minutes=strp_time.minute,
                                          seconds=strp_time.second)
                except:
                    self.timeleft=None
                self.resources_label.setText(str(self.session.hash['node']))
            else:
                self.time.setText('Not defined')
                self.resources_label.setText('Not defined')

        if self.status is Status.KILLING:
            self.connect_btn.setEnabled(False)
            self.share_btn.setEnabled(False)
            self.kill_btn.setEnabled(False)

        if self.status is Status.FINISHED:
            self.connect_btn.setEnabled(False)
            self.share_btn.setEnabled(False)
            self.kill_btn.setEnabled(True)

        self.status_label.setText(str(self.status))
        self.status_label.update()

    def kill_all_threads(self):
        if self.kill_thread:
            if not self.kill_thread.isFinished():
                logger.debug("killing kill display thread")
                self.kill_thread.terminate()
