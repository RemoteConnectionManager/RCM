# python import
from datetime import timedelta, datetime

# pyqt5
from PyQt5.QtCore import pyqtSignal, QTimer, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QFrame, QLabel, \
    QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog

# local includes
from client.utils.pyinstaller_utils import resource_path
from client.log.logger import logger
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
            strp_time = datetime.strptime(timeleft, "%H:%M:%S")
            self.timeleft = timedelta(hours=strp_time.hour,
                                      minutes=strp_time.minute,
                                      seconds=strp_time.second)
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
        display_hor_layout.setContentsMargins(0, 2, 0, 2)
        display_hor_layout.setSpacing(2)

        display_ver_layout = QVBoxLayout()
        display_ver_layout.setContentsMargins(0, 0, 0, 0)
        display_ver_layout.setSpacing(0)

        display_ver_layout.addLayout(display_hor_layout)

        self.setLayout(display_ver_layout)

        name = QLabel(self)
        name.setText(str(self.display_name)[:16])
        display_hor_layout.addWidget(name)

        self.status_label = QLabel(self)
        self.status_label.setText(str(self.status))
        display_hor_layout.addWidget(self.status_label)

        self.time = QLabel(self)
        if self.timeleft is not None:
            self.time.setText(str(self.timeleft))
        else:
            self.time.setText("Not defined")
        display_hor_layout.addWidget(self.time)

        timer = QTimer(self)
        timer.timeout.connect(self.time_update)
        timer.start(1000)

        self.resources_label = QLabel(self)
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
            self.parent.remote_connection_manager.vncsession(self.session,
                                                             gui_cmd=self.enable_connect_button)
        except:
            logger.error("Failed to connecting to remote display " + str(self.display_name))

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
                    out_file.write("port={0}\n".format(5900 + int(self.session.hash['display'])))
                    out_file.write("password={0}\n".format(self.session.hash['vncpassword']))
        except Exception as e:
            logger.error(e)
            logger.error("Failed to share display " + str(self.display_name))

    def kill_display(self):
        """
        Kill the display running on the server
        :return:
        """
        current_status = self.status
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
            self.timeleft = self.timeleft - timedelta(seconds=1)
            self.time.setText(str(self.timeleft))
            self.time.update()

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
        logger.debug("updating display widget for status " + str(self.status))

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

                strp_time = datetime.strptime(timeleft, "%H:%M:%S")
                self.timeleft = timedelta(hours=strp_time.hour,
                                          minutes=strp_time.minute,
                                          seconds=strp_time.second)
                self.resources_label.setText(str(self.session.hash['node']))
            else:
                self.time.setText('Not defined')
                self.resources_label.setText('Not defined')

        if self.status is Status.KILLING:
            self.connect_btn.setEnabled(False)
            self.share_btn.setEnabled(False)
            self.kill_btn.setEnabled(False)
            if self.session:
                timeleft = str(self.session.hash['timeleft'])
                self.time.setText(timeleft)

                strp_time = datetime.strptime(timeleft, "%H:%M:%S")
                self.timeleft = timedelta(hours=strp_time.hour,
                                          minutes=strp_time.minute,
                                          seconds=strp_time.second)
                self.resources_label.setText(str(self.session.hash['node']))
            else:
                self.time.setText('Not defined')
                self.resources_label.setText('Not defined')

        if self.status is Status.FINISHED:
            self.connect_btn.setEnabled(False)
            self.share_btn.setEnabled(False)
            self.kill_btn.setEnabled(True)
            self.time.setText('Not defined')
            self.resources_label.setText('Not defined')

        self.status_label.setText(str(self.status))
        self.status_label.update()

    def kill_all_threads(self):
        if self.kill_thread:
            if not self.kill_thread.isFinished():
                logger.debug("killing kill display thread")
                self.kill_thread.terminate()
