# pyqt5
from PyQt5.QtWidgets import QLabel, QDialog, \
    QHBoxLayout, QVBoxLayout, QGroupBox, QPushButton, QCheckBox

# local includes


class QEditSettingsDialog(QDialog):

    def __init__(self, parent):
        QDialog.__init__(self, parent)

        self.setWindowTitle("Edit settings")
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

        log_level_hlayout = QHBoxLayout()
        log_level = QLabel(self)
        log_level.setText('Debug log level:')
        log_level_hlayout.addWidget(log_level)

        log_level_hlayout.addSpacing(250)
        log_level_checkbox = QCheckBox("", self)
        log_level_hlayout.addWidget(log_level_checkbox)

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

        group_box.setLayout(inner_vlayout)
        outer_grid_layout.addWidget(group_box)
        outer_grid_layout.addSpacing(10)
        outer_grid_layout.addLayout(last_hor_layout)
        self.setLayout(outer_grid_layout)

    def on_save(self):
        self.close()
