# stdlib
import json
import sys
import re
from collections import OrderedDict

# pyqt5
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QLabel, QLineEdit, QDialog, QComboBox, \
    QHBoxLayout, QVBoxLayout, QPushButton, \
    QApplication, QTabWidget, QWidget, QSlider


class QDisplayDialog(QDialog):

    def __init__(self, dictionary):
        QDialog.__init__(self)

        self.schedulers = OrderedDict(sorted(dictionary["SCHEDULER"].items()))
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
        hor_layout.addStretch(1)
        hor_layout.addWidget(ok_button)

        # Cancel button
        cancel_button = QPushButton('Cancel', self)
        hor_layout.addWidget(cancel_button)
        hor_layout.addStretch(1)

        main_layout.addWidget(self.tabs)
        main_layout.addLayout(hor_layout)
        self.setLayout(main_layout)


class QJobWidget(QWidget):
    def __init__(self, schedulers):
        QWidget.__init__(self)
        self.switcher = {
            'combobox': self.ComboBox,
            'slider': self.Slider
        }
        self.schedulers = schedulers
        self.hided_widgets = {}
        self.gui_widgets = []

        self.main_layout = QVBoxLayout()

        self.recursive_init_ui(self.schedulers, self.main_layout, [], "SCHEDULER")

        print(self.hided_widgets.keys())
        self.setLayout(self.main_layout)

    def recursive_init_ui(self, d, parent_layout, parent_values=[], path=" "):
        try:
            values = d.get('values', [])
            if not values:
                choices = d.get('choices', [])
                if choices:
                    values = choices.keys()

            if values:
                gui_widget = self.create_widget(parent_layout,
                                                d.get('name'),
                                                d.get('type'),
                                                values,
                                                path)
                gui_widget.parent = self
                self.gui_widgets.append(gui_widget)

            if 'list' in d or 'choices' in d:
                count = 0

                if 'list' in d:
                    items = d['list']
                else:
                    items = d['choices']

                nested_widget = QWidget()
                nested_ver_layout = QVBoxLayout()
                nested_ver_layout.setContentsMargins(0, 0, 0, 0)
                # nested_ver_layout.setSpacing(10)
                nested_widget.setLayout(nested_ver_layout)
                parent_layout.addWidget(nested_widget)

                for key, value in items.items():
                    # choices
                    if 'choices' in d:
                        count += 1
                        hided_widget = QWidget()
                        hided_ver_layout = QVBoxLayout()
                        hided_ver_layout.setContentsMargins(0, 0, 0, 0)
                        # hided_ver_layout.setSpacing(10)
                        hided_widget.setLayout(hided_ver_layout)
                        nested_ver_layout.addWidget(hided_widget)

                        if count > 1:
                            hided_widget.hide()

                        widget_path = path + "." + key
                        print("choice: " + widget_path)
                        self.hided_widgets[widget_path] = hided_widget

                        self.recursive_init_ui(value, hided_ver_layout, values, path + "." + key)
                    # list
                    else:
                        self.recursive_init_ui(value, nested_ver_layout, values, path + "." + key)
            else:
                return
        except Exception as e:
             print(e)

    def create_widget(self, parent_layout, name=None, type=None, par=None, path=''):
        if type is not None:

            # create a new widget
            main_widget = QWidget()

            # create a new layout
            hor_layout = QHBoxLayout()

            # create the inner widgets (label, combobox or slider)
            label_widget = QLabel("%s:" % name)
            inner_widget = self.switcher[type](par, path)

            # layouts the widget
            hor_layout.addWidget(label_widget)
            hor_layout.addWidget(inner_widget)

            main_widget.setLayout(hor_layout)

            parent_layout.addWidget(main_widget)

            return inner_widget

    def remove_widget(self, id):
        self.widgets[id].hide()

        # then we remove it from the layout and from the dictionary
        self.main_layout.removeWidget(self.widgets[id])
        self.widgets[id].setParent(None)
        del self.widgets[id]

    class ComboBox(QComboBox):
        def __init__(self, values=None, path=''):
            QComboBox.__init__(self)
            self.parent = None
            self.choices = values
            self.path = path
            self.currentIndexChanged.connect(lambda: self.combo_box_change(self.choices))
            self.addItems(values)
            self.setCurrentIndex(0)

        @pyqtSlot()
        def combo_box_change(self, values):
            if self.currentText() in values:
                key = self.path + "." + self.currentText()
                print("switched to " + key)

                if self.parent:
                    if key in self.parent.hided_widgets:
                        self.parent.hided_widgets[key].show()

                    for choice in self.choices:
                        if choice != self.currentText():
                            new_key = self.path + "." + choice
                            if new_key in self.parent.hided_widgets:
                                self.parent.hided_widgets[new_key].hide()

    class Slider(QWidget):
        def __init__(self, values=None, path='', value_type=""):
            QWidget.__init__(self)
            self.parent = None

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
