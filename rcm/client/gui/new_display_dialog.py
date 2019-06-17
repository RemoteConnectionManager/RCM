# stdlib
import json
import sys
import re
import time
import traceback

# pyqt5
from PyQt5.QtCore import Qt, pyqtSlot, QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QLabel, QLineEdit, QDialog, QComboBox, \
    QHBoxLayout, QVBoxLayout, QPushButton, \
    QApplication, QTabWidget, QWidget, QSlider, QSizePolicy, QFrame



class QDisplayDialog(QDialog):

    def __init__(self, display_dialog_ui, callback=None,
                 name_choices=('SCHEDULER', 'SCHEDULER.QUEUE', 'SERVICE', 'SERVICE.COMMAND')):
        QDialog.__init__(self)

        if callback:
            self.callback = callback
        else:
            self.callback = self.print_callback

        self.name_choices = name_choices

        self.display_dialog_ui = display_dialog_ui
        self.tabs = QTabWidget(self)
        self.job = None
        self.choices = dict()
        self.display_name = ''

        self.setWindowTitle("New display")
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.init_ui()

    def init_ui(self):
        self.job = QJobWidget(self.display_dialog_ui)

        # Add the job tab
        self.tabs.addTab(self.job, "Job")

        # Ok button
        bottom_layout = QHBoxLayout()
        ok_button = QPushButton('Ok', self)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(ok_button)

        # Cancel button
        cancel_button = QPushButton('Cancel', self)
        cancel_button.clicked.connect(self.reject)
        bottom_layout.addWidget(cancel_button)
        bottom_layout.addStretch(1)

        # add widgets and the ok-cancel layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

        ok_button.clicked.connect(self.on_ok)

    def on_ok(self):
        self.choices = dict()

        for key, value in self.job.choices.items():
            self.choices[key] = value

        for key, container_widget in self.job.containers.items():
            if not container_widget.isHidden():
                for key2, value2 in container_widget.choices.items():
                    self.choices[key2] = value2


        for key in self.name_choices:
            if key in self.choices:
                if self.display_name:
                    separator = '.'
                else:
                    separator = ''
                self.display_name += (separator + self.choices[key])

        self.callback(self.choices)

    def print_callback(self,choices):
        for key, value in choices.items():
            print(key + " : " + value)

        self.accept()


class QContainerWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        # list of choices made by the user in the listbox widgets owned by this container
        self.choices = dict()
        # list of containers that are children of this container
        self.childs = list()
        # list of gui Qt widgets owned by this Qt container
        self.widgets = list()


class QJobWidget(QContainerWidget):
    def __init__(self, display_dialog_ui):
        QContainerWidget.__init__(self)

        # dictionary that stores all the containers of this widget
        self.containers = dict()

        self.display_dialog_ui = display_dialog_ui
        self.main_layout = None

        self.init_ui()

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.main_layout = QVBoxLayout()

        for key, childs in self.display_dialog_ui.items():
            self.recursive_init_ui(childs, self, self.main_layout, key, key)

        self.main_layout.addStretch(1)
        self.setLayout(self.main_layout)

    def recursive_init_ui(self, d, parent_widget, parent_layout, path="", var=""):
        try:
            if not isinstance(d, dict):
                return

            values = d.get('values', None)
            label = d.get('label', None)
            widget_type = d.get('type', None)
            description = d.get('description', None)

            if values:
                gui_widget = create_hor_composite_widget(parent_widget,
                                                         parent_layout,
                                                         label,
                                                         widget_type,
                                                         values,
                                                         path,
                                                         var,
                                                         description )
                gui_widget.parent = self
                gui_widget.update()
                parent_widget.widgets.append(gui_widget)

            if 'children' in d:
                items = d['children']
            elif 'values' in d:
                items = d['values']
            else:
                return

            count = 0

            nested_widget = QWidget()
            nested_ver_layout = QVBoxLayout()
            nested_ver_layout.setContentsMargins(0, 0, 0, 0)
            nested_widget.setLayout(nested_ver_layout)
            parent_layout.addWidget(nested_widget)

            if isinstance(items, dict):
                for key, value in items.items():
                    if 'values' in d:
                        count += 1
                        hided_widget = QContainerWidget()
                        hided_ver_layout = QVBoxLayout()
                        hided_ver_layout.setContentsMargins(0, 0, 0, 0)
                        hided_widget.setLayout(hided_ver_layout)
                        nested_ver_layout.addWidget(hided_widget)

                        if count > 1:
                            hided_widget.hide()

                        if isinstance(parent_widget, QContainerWidget) and not isinstance(parent_widget, QJobWidget)\
                                and parent_widget.isHidden():
                            hided_widget.hide()

                        widget_path = path + "." + key
                        self.containers[widget_path] = hided_widget

                        if isinstance(parent_widget, QContainerWidget):
                            parent_widget.childs.append(hided_widget)

                        self.recursive_init_ui(value,
                                               hided_widget,
                                               hided_ver_layout,
                                               path + "." + key,
                                               var)
                    else:
                        self.recursive_init_ui(value,
                                               parent_widget,
                                               nested_ver_layout,
                                               path + "." + key,
                                               var + "." + key)
        except Exception as e:
            print(e, traceback.format_exc())


def create_hor_composite_widget(parent_widget,
                                parent_layout,
                                label=None,
                                widget_type=None,
                                parameters=None,
                                path='',
                                var='',
                                description=''):
    """
    Create a horizontal composite widget to be added in the main vertical layout
    The composite widget is made of a qlabel + an interactive gui widget
    :param parent_widget:
    :param parent_layout:
    :param label:
    :param widget_type:
    :param parameters:
    :param path:
    :param var:
    :return:
    """
    if widget_type:
        main_widget = QWidget()
        hor_layout = QHBoxLayout()

        if label:
            label_widget = QLabel("%s:" % label)
            hor_layout.addWidget(label_widget)

        qvar_widget = widget_factory(widget_type)(parameters, path, var, parent_widget, description)

        hor_layout.addWidget(qvar_widget)
        main_widget.setLayout(hor_layout)
        parent_layout.addWidget(main_widget)

        return qvar_widget


def show_childs(container_widget):
    if container_widget.childs:
        for child in container_widget.childs:
            show_childs(child)
    for w in container_widget.widgets:
        if w.__class__.__name__ == 'ComboBox':
            if callable(getattr(w, 'combo_box_change', None)):
                w.combo_box_change(w.currentText())


def hide_childs(container_widget):
    if container_widget.childs:
        for child in container_widget.childs:
            child.hide()
            hide_childs(child)


def widget_factory(widget_type):
    """
    Create a interactive gui widget from string (factory pattern)
    :param widget_type:
    :return:
    """

    # nested class
    class ComboBox(QComboBox):
        def __init__(self, values=None, path='', var='', parent_widget=None, description=None):
            QComboBox.__init__(self)
            self.parent_widget = parent_widget
            self.var = var
            self.parent = None
            self.choices = values
            self.path = path
            self.currentIndexChanged.connect(lambda: self.combo_box_change(self.choices))
            self.addItems(values)
            count = 0
            for v in values:
                choice_description = values[v].get('description','')
                if choice_description:
                    self.setItemData(count, choice_description, Qt.ToolTipRole)
                count += 1
            self.setCurrentIndex(0)
            if description:
                self.setToolTip(description)

        def update(self):
            self.currentIndexChanged.emit(0)

        @pyqtSlot()
        def combo_box_change(self, values):
            if self.currentText() in values:
                key = self.path + "." + self.currentText()
                # print("switched to " + key)

                if self.parent_widget:
                    self.parent_widget.choices[self.var] = self.currentText()

                if self.parent:
                    if key in self.parent.containers:
                        self.parent.containers[key].show()
                        # show only the first child objects
                        show_childs(self.parent.containers[key])

                    for choice in self.choices:
                        if choice != self.currentText():
                            new_key = self.path + "." + choice
                            if new_key in self.parent.containers:
                                self.parent.containers[new_key].hide()
                                # hide all the child objects
                                hide_childs(self.parent.containers[new_key])

    class Divider(QFrame):
        def __init__(self, values=None, path='', var='', parent_widget=None, description=None):
            QFrame.__init__(self)
            self.setFrameShape(QFrame.HLine)
            self.setFrameShadow(QFrame.Sunken)
            self.var = var
            self.path = path

        def update(self):
            return

    class Slider(QWidget):
        def __init__(self, values=None, path='', var='', parent_widget=None, description=None):
            QWidget.__init__(self)
            self.parent = None
            self.var = var
            self.path = path
            self.parent_widget = parent_widget
            self.values = values

            main_layout = QHBoxLayout()

            self.slider_edit = QLineEdit()
            self.slider_edit.setText(str(values.get('min')))

            self.slider = QSlider(Qt.Horizontal)
            self.slider.setFixedWidth(100)
            self.slider.setMinimum(values.get('min'))
            self.slider.setMaximum(values.get('max'))
            if 'description' in values:
                self.slider.setToolTip(values['description'])
            else:
                if description:
                    self.slider.setToolTip(description)

            self.slider_edit.textChanged.connect(self.slider_edit_change)
            self.slider.valueChanged.connect(self.slider_change)

            main_layout.addStretch(1)
            main_layout.addWidget(self.slider_edit)
            main_layout.addWidget(self.slider)

            self.setLayout(main_layout)

        def update(self):
            self.slider.valueChanged.emit(self.values.get('min'))

        @pyqtSlot()
        def slider_edit_change(self):
            num = re.search("[0-9]*", self.sender().text()).group(0)
            if not num:
                return
            elif int(num) < self.slider.minimum():
                num = str(self.slider.minimum())
            elif int(num) > self.slider.maximum():
                num = str(self.slider.maximum())
            text = str(num)
            self.sender().setText(text)
            self.slider.setValue(int(num))

        @pyqtSlot()
        def slider_change(self):
            text = str(self.slider.value())
            self.slider_edit.setText(text)

            if self.parent_widget:
                self.parent_widget.choices[self.var] = text

    def sec_to_time(seconds):
        return time.strftime('%H:%M:%S', time.gmtime(seconds))

    def time_to_sec(time):
        sec=0
        mul=1
        for t in reversed(list(map(int, re.findall('\d+', str(time))))[-3:]):
            sec = sec + mul * t
            mul = mul * 60
        return int(sec)

    class TimeSlider(Slider):

        def __init__(self, values=None, path='', var='', parent_widget=None):

            Slider.__init__(self,
                            values={'min' :time_to_sec(values.get('min', 0)),
                                    'max' :time_to_sec(values.get('max', 1)) },
                            path=path,
                            var=var,
                            parent_widget=parent_widget)

            qregex = QRegExp("^(?:(?:([01]?\d|2[0-3]):)?([0-5]?\d):)?([0-5]?\d)$")
            validator = QRegExpValidator(qregex)
            self.slider_edit.setValidator(validator)

        @pyqtSlot()
        def slider_change(self):
            text = str(sec_to_time(self.slider.value()))
            self.slider_edit.setText(text)

            if self.parent_widget:
                self.parent_widget.choices[self.var] = text

        @pyqtSlot()
        def slider_edit_change(self):
            num = time_to_sec(self.sender().text())
            if not num:
                return
            elif num < self.slider.minimum():
                num = self.slider.minimum()
            elif num > self.slider.maximum():
                num = self.slider.maximum()

            self.slider.setValue(int(num))


    # factory build commands
    if widget_type == "combobox":
        return ComboBox
    if widget_type == "slider":
        return Slider
    if widget_type == "timeslider":
        return TimeSlider
    if widget_type == "divider":
        return Divider

