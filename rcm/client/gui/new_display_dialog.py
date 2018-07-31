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

        self.schedulers = OrderedDict(sorted(dictionary["Scheduler"].items()))
        # self.queues = {}

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
        self.switcher = {
            'Account': self.ComboBox,
            'CPU': lambda values: self.Slider(values, value_type="c"),
            'Queue': lambda values: self.ComboBox(values, iscomplex=True),
            'Memory': lambda values: self.Slider(values, value_type="Gb"),
            'Scheduler': lambda values: self.ComboBox(values, iscomplex=True),
        }
        self.schedulers = schedulers
        self.widgets = {}

        self.main_layout = QVBoxLayout()

        self.recursive_init_ui(self.schedulers)
        self.setLayout(self.main_layout)

    def recursive_init_ui(self, d):
        try:
            if 'values' in d:
                self.create_widget(d.get('type'), d.get('values'))
            elif 'sons' in d:
                self.create_widget(d.get('type'), d.get('sons'))
                for k in d.get('sons'):
                    self.recursive_init_ui(d.get('sons')[k])
            else:
                return
        except Exception as e:
            print("Exception:{0}"
                  "\n{1}".format(type(e), e))

    def create_widget(self, type=None, par=None):
        if type is not None:
            label = QLabel("%s:" % type)

            main_widget = QWidget()
            layout = QHBoxLayout(main_widget)
            layout.addWidget(label)
            layout.addWidget(self.switcher[type](par))

            self.main_layout.addWidget(main_widget)
            self.widgets['type'] = main_widget

    def remove_widget(self, id):
        self.widgets[id].hide()

        # then we remove it from the layout and from the dictionary
        self.main_layout.removeWidget(self.widgets[id])
        self.widgets[id].setParent(None)
        del self.widgets[id]

    class ComboBox(QComboBox):
        def __init__(self, values=None, iscomplex=False):
            QComboBox.__init__(self)
            print(values)
            self.son = values
            if iscomplex:

                self.currentIndexChanged.connect(lambda: self.combo_box_change(self.son))
            self.addItems(values)
            self.setCurrentIndex(0)

        @pyqtSlot()
        def combo_box_change(self, values):
            if self.currentText() in values:
                print("RECURISVE!")
                # self.recursive_init_ui(values.get(self.currentText()))

    class Slider(QWidget):
        def __init__(self, values=None, value_type=""):
            QWidget.__init__(self)
            print(values)
            main_layout = QHBoxLayout()

            self.slider_edit = QLineEdit()
            self.slider_edit.setText("{0}{1}".format(values.get('min'), value_type))

            self.slider = QSlider(Qt.Horizontal)
            self.slider.setMinimum(values.get('min'))
            self.slider.setMaximum(values.get('max'))

            self.slider_edit.editingFinished.connect(lambda: self.slider_edit_change(value_type))
            self.slider.valueChanged.connect(lambda: self.slider_change(value_type))

            main_layout.addWidget(self.slider_edit)
            main_layout.addWidget(self.slider)

            self.setLayout(main_layout)

        @pyqtSlot()
        def slider_edit_change(self, value_type=""):
            num = re.search("[0-9]*", self.sender().text()).group(0)
            if not num:
                return
            elif int(num) < self.slider.minimum():
                num = str(self.slider.minimum())
            elif int(num) > self.slider.maximum():
                num = str(self.slider.maximum())
            text = "{0}{1}".format(num, value_type)
            self.sender().setText(text)
            self.slider.blockSignals(True)
            self.slider.setValue(int(num))
            self.slider.blockSignals(False)

        @pyqtSlot()
        def slider_change(self, line_edit, value_type=""):
            text = "{0}{1}".format(self.slider.value(), value_type)
            self.slider_edit.blockSignals(True)
            self.slider_edit.setText(text)
            self.slider_edit.blockSignals(False)


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
    dictionary = json.load(open("scheduler.json"), object_pairs_hook=OrderedDict)
    dictionary = OrderedDict(sorted(dictionary.items()))

    display_dialog = QDisplayDialog(dictionary)
    display_dialog.show()
    sys.exit(app.exec_())
