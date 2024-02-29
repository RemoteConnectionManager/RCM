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

import collections
import json
import os
import re

# pyqt
try:
    from PyQt6.QtWidgets import QLabel, QLineEdit, QDialog, QComboBox, \
        QHBoxLayout, QVBoxLayout, QGroupBox, QGridLayout, QPushButton
    from PyQt6.QtGui import QGuiApplication
    PyQt = 6
except ImportError:
    from PyQt5.QtWidgets import QLabel, QLineEdit, QDialog, QComboBox, \
        QHBoxLayout, QVBoxLayout, QGroupBox, QGridLayout, QPushButton
    from PyQt5.QtWidgets import QDesktopWidget
    PyQt = 5


# local includes
from client.miscellaneous.logger import logger
from client.miscellaneous.config_parser import parser, config_file_name


class QDisplayDialog(QDialog):

    def __init__(self, display_names, platform_config):
        QDialog.__init__(self)

        self.display_name = ""
        self.display_names = display_names
        self.display_size_list = collections.deque(maxlen=5)

        # current selections
        self.session_queue = None
        self.session_vnc = None
        self.display_size = None

        # combo
        self.session_queue_combo = None
        self.session_vnc_combo = None
        self.display_combo = None

        try:
            self.session_queues = platform_config.config['queues'].keys()
            self.session_vncs = platform_config.config['vnc_commands'].keys()
        except:
            self.session_queues = []
            self.session_vncs = []
            logger.error("Failed to parse the server platform config")

        self.setWindowTitle("New display")
        self.init_ui()

    def init_ui(self):
        """
        Initialize the interface
        :return:
        """

        try:
            display_size_list = parser.get('DisplaySizeField', 'displaysizelist')
            self.display_size_list = collections.deque(json.loads(display_size_list), maxlen=5)
        except Exception:
            self.display_size_list.appendleft("full_screen")
            self.display_size_list.appendleft("1024x968")

        # create the grid layout
        grid_layout = QGridLayout()

        # Create session layout
        session_name = QLabel(self)
        session_name.setText('session name:')

        grid_layout.addWidget(session_name, 1, 0)

        session_line = QLineEdit(self)
        session_line.setObjectName('session_line')
        grid_layout.addWidget(session_line, 1, 1)

        session_queue = QLabel(self)
        session_queue.setText('Select queue:')

        self.session_queue_combo = QComboBox(self)
        self.session_queue_combo.addItems(self.session_queues)
        grid_layout.addWidget(session_queue, 2, 0)
        grid_layout.addWidget(self.session_queue_combo, 2, 1)

        session_vnc = QLabel(self)
        session_vnc.setText('Select wm+vnc:')

        self.session_vnc_combo = QComboBox(self)
        self.session_vnc_combo.addItems(self.session_vncs)
        grid_layout.addWidget(session_vnc, 3, 0)
        grid_layout.addWidget(self.session_vnc_combo, 3, 1)

        display_label = QLabel(self)
        display_label.setText('Display size:')

        self.display_combo = QComboBox(self)
        self.display_combo.setEditable(True)
        self.display_combo.addItems(list(self.display_size_list))

        grid_layout.addWidget(display_label, 4, 0)
        grid_layout.addWidget(self.display_combo, 4, 1)

        # Ok button
        hor_layout = QHBoxLayout()
        ok_button = QPushButton('Ok', self)
        ok_button.clicked.connect(self.on_ok)
        hor_layout.addStretch(1)
        hor_layout.addWidget(ok_button)

        # Cancel button
        cancel_button = QPushButton('Cancel', self)
        cancel_button.clicked.connect(self.reject)
        hor_layout.addWidget(cancel_button)
        hor_layout.addStretch(1)

        group_box = QGroupBox("Display options:")
        group_box.setLayout(grid_layout)

        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(group_box)
        dialog_layout.addSpacing(10)
        dialog_layout.addLayout(hor_layout)
        self.setLayout(dialog_layout)

    def update_config_file(self):
        """
        Update the config file with the display size list
        :return:
        """
        if not parser.has_section('DisplaySizeField'):
            parser.add_section('DisplaySizeField')

        parser.set('DisplaySizeField', 'displaysizelist', json.dumps(list(self.display_size_list)))

        try:
            config_file_dir = os.path.dirname(config_file_name)
            if not os.path.exists(config_file_dir):
                os.makedirs(config_file_dir)

            with open(config_file_name, 'w') as config_file:
                parser.write(config_file)
        except:
            logger.error("failed to dump the display size list in the configuration file")

    def on_ok(self):
        """
        :return: Return accept signal if the display name is unique
        """

        session_line = self.findChild(QLineEdit, 'session_line')
        display_name = str(session_line.text())

        # if the display_name is empty, it is set to test
        # if it is not empty we validate it using a regex
        if not re.match(r'^[\w\_\s]{0,16}$', display_name):
            logger.error("Invalid display name: only alphanumeric "
                         "plus underscore plus space characters "
                         "are allowed for a maximum of 16 characters")
            return
        if display_name == "":
            self.display_name = "test"
        else:
            self.display_name = display_name

        # if the display name already exists, it returns
        if self.display_name in self.display_names:
            logger.error("session " + str(self.display_name) + " already exists")
            return

        self.session_queue = str(self.session_queue_combo.currentText())
        self.session_vnc = str(self.session_vnc_combo.currentText())
        self.display_size = str(self.display_combo.currentText())

        # add a new display size if it's fine for us in the combobox for the next time
        if self.display_size not in list(self.display_size_list):
            if re.match(r'^\d{1,5}x\d{1,5}$', self.display_size):
                self.display_size_list.appendleft(self.display_size)
            else:
                logger.error("Invalid display size")
                return

        # convert full screen in the format width x height
        if self.display_size == "full_screen":
            if PyQt == 6:
                screen_width = QGuiApplication.primaryScreen().availableGeometry().width()
                screen_height = QGuiApplication.primaryScreen().availableGeometry().height()
            if PyQt == 5:
                screen_width = QDesktopWidget().width()
                screen_height = QDesktopWidget().height()
            self.display_size = str(screen_width) + "x" + str(screen_height)

        logger.info("session queue: " + self.session_queue + "; " +
                    "session vnc: " + self.session_vnc + "; " +
                    "display size: " + self.display_size + ";")

        self.update_config_file()
        self.accept()
