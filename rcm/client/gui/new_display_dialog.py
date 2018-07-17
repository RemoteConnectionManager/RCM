# stdlib
import json
import sys
import logging
import os
import re
from collections import OrderedDict

# pyqt5
from PyQt5.QtCore import Qt, pyqtSlot,QTime

from PyQt5.QtWidgets import QLabel, QLineEdit, QDialog, QComboBox, \
    QHBoxLayout, QVBoxLayout, QGroupBox, QPushButton, \
    QApplication, QTabWidget, QWidget, QSlider, QTimeEdit

# logger init
# logger = logging.getLogger('basic')
# logger.setLevel("DEBUG")
# ch = logging.StreamHandler(sys.stdout)
# formatter = logging.Formatter('[%(levelname)s] %(asctime)s (%(module)s:%(lineno)d %(funcName)s) : %(message)s')
# ch.setFormatter(formatter)
# logger.addHandler(ch)


class QDisplayDialog(QDialog):

    def __init__(self, dictionary):
        QDialog.__init__(self)

        self.schedulers = OrderedDict(sorted(dictionary["schedulers"].items()))
        #self.queues = {}

        self.vnc = {"fluxbox_turbovnc",
                    "kde_turbovnc"}

        self.setWindowTitle("New display")
        self.tabs = QTabWidget(self)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        job = QJobWidget(self.schedulers)
        service = QServiceWidget(self.vnc)

        # Add all various tab
        self.tabs.addTab(job, "Job")
        self.tabs.addTab(service, "Service")

        # Ok button
        hor_layout = QHBoxLayout()
        ok_button = QPushButton('Ok', self)
        # ok_button.clicked.connect(self.on_ok)
        hor_layout.addStretch(1)
        hor_layout.addWidget(ok_button)

        # Cancel button
        cancel_button = QPushButton('Cancel', self)
        # cancel_button.clicked.connect(self.reject)
        hor_layout.addWidget(cancel_button)
        hor_layout.addStretch(1)

        # main_layout.addWidget(service)
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(hor_layout)
        self.setLayout(main_layout)


class QJobWidget(QWidget):
    def __init__(self, schedulers):
        QWidget.__init__(self)
        self.schedulers = schedulers
        self.queues = {}

        self.init_ui()

    def init_ui(self):
        # Initialize JobWidget UI
        job_layout = QVBoxLayout()

        # Scheduler name
        scheduler_layout = QHBoxLayout()
        scheduler_name = QLabel("Scheduler:")
        scheduler_combo = QComboBox(self)
        scheduler_combo.addItems(self.schedulers.keys())
        scheduler_combo.currentIndexChanged.connect(
            lambda: self.scheduler_change(scheduler_combo.currentText()))

        scheduler_layout.addWidget(scheduler_name)
        scheduler_layout.addWidget(scheduler_combo)

        job_layout.addLayout(scheduler_layout)

        # Queue name
        queue_name = QLabel("Queue:")
        self.queue_combo = QComboBox(self)

        # self.scheduler_change(scheduler_combo.currentText())
        #
        # self.queue_combo.addItems(OrderedDict(sorted(self.schedulers[scheduler_combo.currentText()].items())))
        #
        # self.queues = OrderedDict(sorted(self.schedulers[scheduler_combo.currentText()].items()))
        # self.queue_combo.addItems(self.queues)

        self.queue_combo.currentIndexChanged.connect(
            lambda: self.queue_change(self.queue_combo.currentText()))

        queue_layout = QHBoxLayout()
        queue_layout.addWidget(queue_name)
        queue_layout.addWidget(self.queue_combo)

        job_layout.addLayout(queue_layout)

        # Parameters Box
        par_group_box = QGroupBox()
        par_group_box_layout = QVBoxLayout(par_group_box)

        # Memory Slider
        self.memory_label = QLabel("1Gb")
        par_group_box_layout.addWidget(self.memory_label)

        self.memory_slider = QSlider(Qt.Horizontal)
        self.memory_slider.setMinimum(1)
        self.memory_slider.setMaximum(16)
        self.memory_slider.valueChanged.connect(
            lambda: self.slider_change(self.memory_slider, self.memory_label))
        par_group_box_layout.addWidget(self.memory_slider)

        # Core Slider
        self.core_label = QLabel("1c")
        par_group_box_layout.addWidget(self.core_label)

        self.core_slider = QSlider(Qt.Horizontal)
        self.core_slider.setMinimum(1)
        self.core_slider.setMaximum(8)
        self.core_slider.valueChanged.connect(
            lambda: self.slider_change(self.core_slider, self.core_label))
        par_group_box_layout.addWidget(self.core_slider)

        # Time Limit
        time_limit_layout = QHBoxLayout()
        time_limit_label = QLabel("Time Limit:")
        self.time_limit_edit = QTimeEdit()

        time_max = QTime()
        time_max.setHMS(12, 0, 0)
        time_min = QTime()
        time_min.setHMS(0, 0, 1)
        self.time_limit_edit.setDisplayFormat("HH:mm:ss")
        self.time_limit_edit.setTimeRange(time_min, time_max)
        # self.time_limit_edit.timeChanged.connect(lambda: self.time_edit_change(self.time_limit_edit))

        time_limit_layout.addWidget(time_limit_label)
        time_limit_layout.addWidget(self.time_limit_edit)
        par_group_box_layout.addLayout(time_limit_layout)

        # Add "Parameter Box"
        job_layout.addWidget(par_group_box)

        self.setLayout(job_layout)
        self.scheduler_change(scheduler_combo.currentText())

    @pyqtSlot()
    def scheduler_change(self, key=None):
        self.queues = OrderedDict(sorted(self.schedulers[key].items()))
        self.queue_combo.clear()
        self.queue_combo.addItems(self.queues)

    @pyqtSlot()
    def queue_change(self,key=None):
        try:
            queue = OrderedDict(sorted(self.queues[key].items()))
            self.memory_slider.show()
            self.memory_label.show()
            self.memory_slider.setMinimum(queue["min_mem"])
            self.memory_slider.setMaximum(queue["max_mem"])
            self.memory_slider.setValue(queue["value"])
        except Exception as e:
            self.memory_slider.hide()
            self.memory_label.hide()

    @pyqtSlot()
    def slider_change(self, slider, label):
        text = str(slider.value()) + re.search("[a-zA-Z]+$", label.text()).group(0)
        label.setText(text)

    def time_edit_change(self):
        pass


class QServiceWidget(QWidget):
    def __init__(self, vnc):
        QWidget.__init__(self)

        # Initialize serviceWidget UI
        service_layout = QVBoxLayout()

        # VNC name
        vnc_layout = QHBoxLayout()
        vnc_name = QLabel("WM + VNC:")
        vnc_combo = QComboBox(self)
        vnc_combo.addItems(vnc)

        vnc_layout.addWidget(vnc_name)
        vnc_layout.addWidget(vnc_combo)

        service_layout.addLayout(vnc_layout)

        # Display size
        display_layout = QHBoxLayout()
        display_size = QLabel("Display Size")
        display_combo = QComboBox(self)
        display_combo.setEditable(True)
        display_combo.addItems({"1024x986",
                                "fullscreen"})

        display_layout.addWidget(display_size)
        display_layout.addWidget(display_combo)

        service_layout.addLayout(display_layout)
        service_layout.addStretch(1)

        self.setLayout(service_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dictionary = json.load(open("scheduler.json"))
    dictionary = OrderedDict(sorted(dictionary.items()))

    display_dialog = QDisplayDialog(dictionary)
    display_dialog.show()
    sys.exit(app.exec_())
