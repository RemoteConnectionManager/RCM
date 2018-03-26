# stdlib
import uuid

# pyqt5
from PyQt5.QtWidgets import QLabel, QLineEdit, QDialog, QComboBox, \
    QHBoxLayout, QVBoxLayout, QGroupBox, QGridLayout, QPushButton


class QDisplayDialog(QDialog):

    def __init__(self, session_names):
        QDialog.__init__(self)

        self.session_name = ""
        self.session_names = session_names

        self.setWindowTitle("New display")
        self.init_ui()

    def init_ui(self):

        # create the grid layout
        grid_layout = QGridLayout()

        # Create session layout
        session_name = QLabel(self)
        session_name.setText('session name:')
        self.session_line= QLineEdit(self)
        grid_layout.addWidget(session_name, 1, 0)
        grid_layout.addWidget(self.session_line, 1, 1)

        session_queue = QLabel(self)
        session_queue.setText('session queue:')
        self.session_combo = QComboBox(self)
        self.session_combo.addItems(["1","2","3","4"])
        grid_layout.addWidget(session_queue, 2, 0)
        grid_layout.addWidget(self.session_combo, 2, 1)

        display_label = QLabel(self)
        display_label.setText('Display size:')
        self.display_line = QLineEdit(self)
        grid_layout.addWidget(display_label, 3, 0)
        grid_layout.addWidget(self.display_line, 3, 1)

        # Ok button
        hor_layout = QHBoxLayout()
        ok = QPushButton('Ok', self)
        ok.clicked.connect(self.on_ok)
        ok.setFixedHeight(20)
        ok.setFixedWidth(100)
        hor_layout.addStretch(1)
        hor_layout.addWidget(ok)

        # Cancel button
        canc = QPushButton('Cancel', self)
        canc.clicked.connect(self.reject)
        canc.setFixedHeight(20)
        canc.setFixedWidth(100)
        hor_layout.addWidget(canc)
        hor_layout.addStretch(1)

        group_box = QGroupBox()
        group_box.setLayout(grid_layout)

        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(group_box)
        dialog_layout.addSpacing(10)
        dialog_layout.addLayout(hor_layout)
        self.setLayout(dialog_layout)

    def on_ok(self):
        session_name = str(self.session_line.text())

        # if the session_name is empty, it is set to a random uuid
        if session_name == "":
            self.session_name = uuid.uuid4().hex
        else:
            self.session_name = session_name

        # if the session name already exists, it returns
        if self.session_name in self.session_names:
            return

        self.accept()
