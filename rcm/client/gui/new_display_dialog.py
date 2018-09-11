# stdlib
import json
import sys
import re
from collections import OrderedDict

# pyqt5
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QLabel, QLineEdit, QDialog, QComboBox, \
    QHBoxLayout, QVBoxLayout, QPushButton, \
    QApplication, QTabWidget, QWidget, QSlider, QSizePolicy, QFrame


class QDisplayDialog(QDialog):

    def __init__(self, display_dialog_ui):
        QDialog.__init__(self)

        self.display_dialog_ui = display_dialog_ui
        self.tabs = QTabWidget(self)

        self.setWindowTitle("New display")
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.init_ui()

    def init_ui(self):
        job = QJobWidget(self.display_dialog_ui)

        # Add the job tab
        self.tabs.addTab(job, "Job")

        # Ok button
        bottom_layout = QHBoxLayout()
        ok_button = QPushButton('Ok', self)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(ok_button)

        # Cancel button
        cancel_button = QPushButton('Cancel', self)
        bottom_layout.addWidget(cancel_button)
        bottom_layout.addStretch(1)

        # add widgets and the ok-cancel layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)


class QJobWidget(QWidget):
    def __init__(self, display_dialog_ui):
        QWidget.__init__(self)
        self.container_widgets = {}
        self.display_dialog_ui = display_dialog_ui
        self.main_layout = None

        self.init_ui()

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.main_layout = QVBoxLayout()

        for key, childs in self.display_dialog_ui.items():
            self.recursive_init_ui(childs, self.main_layout, [], key)

        self.main_layout.addStretch(1)
        self.setLayout(self.main_layout)

    def recursive_init_ui(self, d, parent_layout, parent_values=[], path=""):
        try:
            values = d.get('values', [])
            if not values:
                choices = d.get('choices', [])
                if choices:
                    values = choices.keys()

            if values:
                gui_widget = create_hor_composite_widget(parent_layout,
                                                         d.get('label'),
                                                         d.get('type'),
                                                         values,
                                                         path)
                gui_widget.parent = self

            if 'list' in d or 'choices' in d:
                count = 0

                if 'list' in d:
                    items = d['list']
                else:
                    items = d['choices']

                nested_widget = QWidget()
                nested_ver_layout = QVBoxLayout()
                nested_ver_layout.setContentsMargins(0, 0, 0, 0)
                #nested_ver_layout.setSpacing(0)
                nested_widget.setLayout(nested_ver_layout)
                parent_layout.addWidget(nested_widget)

                for key, value in items.items():
                    # choices
                    if 'choices' in d:
                        count += 1
                        hided_widget = QWidget()
                        hided_ver_layout = QVBoxLayout()
                        hided_ver_layout.setContentsMargins(0, 0, 0, 0)
                        #hided_ver_layout.setSpacing(0)
                        hided_widget.setLayout(hided_ver_layout)
                        nested_ver_layout.addWidget(hided_widget)

                        if count > 1:
                            hided_widget.hide()

                        widget_path = path + "." + key
                        print("choice: " + widget_path)
                        self.container_widgets[widget_path] = hided_widget

                        self.recursive_init_ui(value, hided_ver_layout, values, path + "." + key)
                    # list
                    else:
                        self.recursive_init_ui(value, nested_ver_layout, values, path + "." + key)
            else:
                return
        except Exception as e:
             print(e)


def create_hor_composite_widget(parent_layout,
                                label=None,
                                widget_type=None,
                                parameters=None,
                                path=''):
    """
    Create a horizontal composite widget to be added in the main vertical layout
    The composite widget is made of a qlabel + an interactive gui widget
    :param parent_layout:
    :param label:
    :param widget_type:
    :param parameters:
    :param path:
    :return:
    """
    if widget_type:
        main_widget = QWidget()
        hor_layout = QHBoxLayout()

        if label:
            label_widget = QLabel("%s:" % label)
            hor_layout.addWidget(label_widget)

        qvar_widget = widget_factory(widget_type)(parameters, path)

        hor_layout.addWidget(qvar_widget)
        main_widget.setLayout(hor_layout)
        parent_layout.addWidget(main_widget)

        return qvar_widget


def widget_factory(widget_type):
    """
    Create a interactive gui widget from string (factory pattern)
    :param widget_type:
    :return:
    """

    # nested class
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
                    if key in self.parent.container_widgets:
                        self.parent.container_widgets[key].show()

                    for choice in self.choices:
                        if choice != self.currentText():
                            new_key = self.path + "." + choice
                            if new_key in self.parent.container_widgets:
                                self.parent.container_widgets[new_key].hide()

    class Divider(QFrame):
        def __init__(self, values=None, path=''):
            QFrame.__init__(self)
            self.setFrameShape(QFrame.HLine)
            self.setFrameShadow(QFrame.Sunken)

    class Slider(QWidget):
        def __init__(self, values=None, path=''):
            QWidget.__init__(self)
            self.parent = None

            main_layout = QHBoxLayout()

            self.slider_edit = QLineEdit()
            self.slider_edit.setText(str(values.get('min')))

            self.slider = QSlider(Qt.Horizontal)
            self.slider.setFixedWidth(100)
            self.slider.setMinimum(values.get('min'))
            self.slider.setMaximum(values.get('max'))

            self.slider_edit.textChanged.connect(self.slider_edit_change)
            self.slider.valueChanged.connect(self.slider_change)

            main_layout.addStretch(1)
            main_layout.addWidget(self.slider_edit)
            main_layout.addWidget(self.slider)

            self.setLayout(main_layout)

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

    # factory build commands
    if widget_type == "combobox":
        return ComboBox
    if widget_type == "slider":
        return Slider
    if widget_type == "divider":
        return Divider


if __name__ == "__main__":
    app = QApplication(sys.argv)
    display_dialog_ui = json.load(open("scheduler.json"), object_pairs_hook=OrderedDict)
    display_dialog = QDisplayDialog(display_dialog_ui)
    display_dialog.show()
    sys.exit(app.exec_())
