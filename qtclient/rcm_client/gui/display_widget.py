# python import
from datetime import timedelta

# pyqt5
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QFrame, QLabel, \
    QVBoxLayout, QHBoxLayout, QPushButton

# local includes
from rcm_client.utils.pyinstaller_utils import resource_path
from rcm_client.log.logger import logger


class QDisplayWidget(QWidget):
    """
    Create a new row (display widget) to be put inside the table shown in the session widget
    """

    terminate = pyqtSignal(str)

    def __init__(self, parent, display_name):
        super(QWidget, self).__init__(parent)

        self.display_name = display_name
        self.remaining_time = timedelta(seconds=3600*3)

        # icons
        self.connect_ico = QIcon()
        self.kill_ico = QIcon()
        self.share_ico = QIcon()

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

        status = QLabel(self)
        status.setText("Pending...")
        display_hor_layout.addWidget(status)

        self.time = QLabel(self)
        self.time.setText(str(self.remaining_time))
        display_hor_layout.addWidget(self.time)

        timer = QTimer(self)
        timer.timeout.connect(self.time_update)
        timer.start(1000)

        resources = QLabel(self)
        resources.setText("1 Node")
        display_hor_layout.addWidget(resources)

        connect_btn = QPushButton(self)
        connect_btn.setIcon(self.connect_ico)
        connect_btn.setToolTip('Connect to the remote display')
        connect_btn.clicked.connect(self.connect_display)
        display_hor_layout.addWidget(connect_btn)

        share_btn = QPushButton(self)
        share_btn.setIcon(self.share_ico)
        share_btn.setToolTip('Share the remote display via file')
        share_btn.clicked.connect(self.share_display)
        display_hor_layout.addWidget(share_btn)

        kill_btn = QPushButton(self)
        kill_btn.setIcon(self.kill_ico)
        kill_btn.setToolTip('Kill the remote display')
        kill_btn.clicked.connect(self.kill_display)
        self.terminate.connect(self.parentWidget().remove_display)

        display_hor_layout.addWidget(kill_btn)

        separator = QFrame(self)
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        display_ver_layout.addWidget(separator)

    def connect_display(self):
        logger.info("Connected to remote display " + str(self.display_name))

    def share_display(self):
        logger.info("Shared display " + str(self.display_name))

    def kill_display(self):
        """
        Kill the display running on the server
        :return:
        """
        self.terminate.emit(self.display_name)

    def time_update(self):
        """
        Update the remaining time of the job running on the server
        :return:
        """
        self.remaining_time = self.remaining_time - timedelta(seconds=1)
        self.time.setText(str(self.remaining_time))
        self.time.update()
