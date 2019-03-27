# std lib
import os
import json
import sys

# pyqt5
from PyQt5.QtWidgets import QLabel, QDialog, QRadioButton, \
    QHBoxLayout, QVBoxLayout, QGroupBox, QPushButton, QCheckBox, QLineEdit

# local includes
from client.miscellaneous.logger import logger, configure_logger
from client.miscellaneous.config_parser import parser, config_file_name, defaults
from client.utils.rcm_enum import Mode


class QEditSettingsDialog(QDialog):

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.settings = {}

        self.setWindowTitle("Edit settings")
        self.load_settings()
        self.init_ui()

    def init_ui(self):
        """
        Initialize the interface
        :return:
        """

        # create the outer layouts
        outer_grid_layout = QVBoxLayout()
        inner_vlayout = QVBoxLayout()

        # Create a group box containing the settings
        group_box = QGroupBox("Settings:")

        # debug log level
        log_level_hlayout = QHBoxLayout()
        log_level = QLabel(self)
        log_level.setText('Debug log level:')
        log_level_hlayout.addWidget(log_level)

        log_level_hlayout.addSpacing(250)
        log_level_hlayout.addStretch(1)
        log_level_checkbox = QCheckBox("", self)
        log_level_checkbox.setObjectName('debug_log_level')
        log_level_checkbox.setChecked(self.settings['debug_log_level'])
        log_level_checkbox.toggled.connect(self.on_log_level_change)
        log_level_hlayout.addWidget(log_level_checkbox)

        # ssh client
        ssh_client_label = QLabel(self)
        ssh_client_label.setText('SSH client:')

        ssh_client_group_box = QGroupBox(self)
        self.ssh_client_btn_int = QRadioButton("internal")
        self.ssh_client_btn_ext = QRadioButton("external")
        self.ssh_client_btn_via = QRadioButton("via")
        if self.settings['ssh_client'] == "internal":
            self.ssh_client_btn_int.setChecked(True)
        elif self.settings['ssh_client'] == "external":
            self.ssh_client_btn_ext.setChecked(True)
        else:
            self.ssh_client_btn_via.setChecked(True)

        ssh_client_vbox = QVBoxLayout()
        ssh_client_vbox.addWidget(self.ssh_client_btn_int)
        ssh_client_vbox.addWidget(self.ssh_client_btn_ext)
        if sys.platform != 'win32':
            ssh_client_vbox.addWidget(self.ssh_client_btn_via)
        ssh_client_vbox.addStretch(1)
        ssh_client_group_box.setLayout(ssh_client_vbox)

        ssh_client_hlayout = QHBoxLayout()
        ssh_client_hlayout.addWidget(ssh_client_label)
        ssh_client_hlayout.addSpacing(250)
        ssh_client_hlayout.addStretch(1)
        ssh_client_hlayout.addWidget(ssh_client_group_box)

        # Preload Command
        preload_command_hlayout = QHBoxLayout()
        preload_command = QLabel(self)
        preload_command.setText('Insert Preload Command:')
        preload_command_hlayout.addWidget(preload_command)

        preload_command_hlayout.addSpacing(250)
        preload_command_hlayout.addStretch(1)
        preload_command_textbox = QLineEdit(self)
        preload_command_textbox.setObjectName('preload_command')
        preload_command_textbox.setText(self.settings['preload_command'])
        preload_command_hlayout.addWidget(preload_command_textbox)

        # Save button
        last_hor_layout = QHBoxLayout()
        save_button = QPushButton('Save', self)
        save_button.clicked.connect(self.on_save)
        last_hor_layout.addStretch(1)
        last_hor_layout.addWidget(save_button)

        # Cancel button
        cancel_button = QPushButton('Cancel', self)
        cancel_button.clicked.connect(self.reject)
        last_hor_layout.addWidget(cancel_button)

        inner_vlayout.addLayout(log_level_hlayout)
        inner_vlayout.addLayout(ssh_client_hlayout)
        inner_vlayout.addLayout(preload_command_hlayout)

        group_box.setLayout(inner_vlayout)
        outer_grid_layout.addWidget(group_box)
        outer_grid_layout.addSpacing(10)
        outer_grid_layout.addLayout(last_hor_layout)
        self.setLayout(outer_grid_layout)

    def on_log_level_change(self, debug):
        configure_logger(Mode.GUI, debug)

    def load_settings(self):
        for k in defaults:
            self.settings[k] = json.loads(parser.get('Settings', k, fallback=defaults[k]))

    def on_save(self):
        if not parser.has_section('Settings'):
            parser.add_section('Settings')

        # update settings values
        self.update_and_apply_settings()
        for k in defaults:
            parser.set('Settings', k, json.dumps(self.settings[k], indent=4))

        try:
            config_file_dir = os.path.dirname(config_file_name)
            if not os.path.exists(config_file_dir):
                os.makedirs(config_file_dir)

            with open(config_file_name, 'w') as config_file:
                parser.write(config_file)
        except Exception:
            logger.error("failed to dump the settings in the configuration file")

        self.close()

    def update_and_apply_settings(self):
        self.settings['debug_log_level'] = self.findChild(QCheckBox, 'debug_log_level').isChecked()
        if self.ssh_client_btn_int.isChecked():
            self.settings['ssh_client'] = "internal"
        elif self.ssh_client_btn_ext.isChecked():
            self.settings['ssh_client'] = "external"
        else:
            self.settings['ssh_client'] = "via"
        self.settings['preload_command'] = self.findChild(QLineEdit, 'preload_command').text()
