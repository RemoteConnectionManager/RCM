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


class QContainer(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.choices = dict()
        self.childs = list()


class QDisplayDialog(QDialog):

    def __init__(self, display_dialog_ui, callback=None):
        QDialog.__init__(self)

        if callback :
            self.callback = callback
        else:
            self.callback=self.print_callback

        self.display_dialog_ui = display_dialog_ui
        self.tabs = QTabWidget(self)
        self.job = None
        self.choices = dict()
        self.display_name = 'Devel'

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

        for key, container_widget in self.job.container_widgets.items():
            if not container_widget.isHidden():
                for key2, value2 in container_widget.choices.items():
                    self.choices[key2] = value2

        self.callback(self.choices)

    def print_callback(self,choices):
        for key, value in self.choices.items():
            print(key + " : " + value)

        self.accept()

        
class QJobWidget(QWidget):
    def __init__(self, display_dialog_ui):
        QWidget.__init__(self)
        self.container_widgets = dict()
        self.gui_widgets = list()
        self.display_dialog_ui = display_dialog_ui
        self.main_layout = None
        self.choices = dict()

        self.init_ui()

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.main_layout = QVBoxLayout()

        for key, childs in self.display_dialog_ui.items():
            self.recursive_init_ui(childs, self, self.main_layout, [], key, key)

        self.main_layout.addStretch(1)
        self.setLayout(self.main_layout)

    def recursive_init_ui(self, d, parent_widget, parent_layout, parent_values=[], path="", var=""):
        try:
            values = d.get('values', None)
            if values:
                gui_widget = create_hor_composite_widget(parent_widget,
                                                         parent_layout,
                                                         d.get('label'),
                                                         d.get('type'),
                                                         values,
                                                         path,
                                                         var)
                gui_widget.parent = self
                gui_widget.update()
                self.gui_widgets.append(gui_widget)

            if 'children' in d or 'values' in d:
                count = 0

                if 'children' in d:
                    items = d['children']
                else:
                    items = d['values']

                nested_widget = QWidget()
                nested_ver_layout = QVBoxLayout()
                nested_ver_layout.setContentsMargins(0, 0, 0, 0)
                nested_widget.setLayout(nested_ver_layout)
                parent_layout.addWidget(nested_widget)

                for key, value in items.items():
                    # choices
                    if 'values' in d:
                        count += 1
                        hided_widget = QContainer()
                        hided_ver_layout = QVBoxLayout()
                        hided_ver_layout.setContentsMargins(0, 0, 0, 0)
                        hided_widget.setLayout(hided_ver_layout)
                        nested_ver_layout.addWidget(hided_widget)

                        if count > 1:
                            hided_widget.hide()

                        if isinstance(parent_widget, QContainer) and parent_widget.isHidden():
                            hided_widget.hide()

                        widget_path = path + "." + key
                        print("choice: " + widget_path)
                        self.container_widgets[widget_path] = hided_widget
                        if isinstance(parent_widget, QContainer):
                            parent_widget.childs.append(hided_widget)

                        self.recursive_init_ui(value,
                                               hided_widget,
                                               hided_ver_layout,
                                               values,
                                               path + "." + key,
                                               var)
                    # list
                    else:
                        self.recursive_init_ui(value,
                                               parent_widget,
                                               nested_ver_layout,
                                               values,
                                               path + "." + key,
                                               var + "." + key)
            else:
                return
        except Exception as e:
            print(e)


def create_hor_composite_widget(parent_widget,
                                parent_layout,
                                label=None,
                                widget_type=None,
                                parameters=None,
                                path='',
                                var=''):
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

        qvar_widget = widget_factory(widget_type)(parameters, path, var, parent_widget)

        hor_layout.addWidget(qvar_widget)
        main_widget.setLayout(hor_layout)
        parent_layout.addWidget(main_widget)

        return qvar_widget


def show_childs(container_widget):
    if container_widget.childs:
        container_widget.childs[0].show()
        show_childs(container_widget.childs[0])


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
        def __init__(self, values=None, path='', var='', parent_widget=None):
            QComboBox.__init__(self)
            self.parent_widget = parent_widget
            self.var = var
            self.parent = None
            self.choices = values
            self.path = path
            self.currentIndexChanged.connect(lambda: self.combo_box_change(self.choices))
            self.addItems(values)
            self.setCurrentIndex(0)

        def update(self):
            self.currentIndexChanged.emit(0)

        @pyqtSlot()
        def combo_box_change(self, values):
            if self.currentText() in values:
                key = self.path + "." + self.currentText()
                print("switched to " + key)

                if self.parent_widget:
                    self.parent_widget.choices[self.var] = self.currentText()

                if self.parent:
                    if key in self.parent.container_widgets:
                        self.parent.container_widgets[key].show()
                        # show only the first child objects
                        show_childs(self.parent.container_widgets[key])

                    for choice in self.choices:
                        if choice != self.currentText():
                            new_key = self.path + "." + choice
                            if new_key in self.parent.container_widgets:
                                self.parent.container_widgets[new_key].hide()
                                # hide all the child objects
                                hide_childs(self.parent.container_widgets[new_key])

    class Divider(QFrame):
        def __init__(self, values=None, path='', var='', parent_widget=None):
            QFrame.__init__(self)
            self.setFrameShape(QFrame.HLine)
            self.setFrameShadow(QFrame.Sunken)
            self.var = var
            self.path = path

        def update(self):
            return

    class Slider(QWidget):
        def __init__(self, values=None, path='', var='', parent_widget=None):
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

    # factory build commands
    if widget_type == "combobox":
        return ComboBox
    if widget_type == "slider":
        return Slider
    if widget_type == "divider":
        return Divider


if __name__ == "__main__":

    app = QApplication(sys.argv)

    import os
    import sys
    root_rcm_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(root_rcm_path)
    sys.path.append(os.path.join(root_rcm_path, 'utils'))
    sys.path.append(os.path.join(root_rcm_path, 'server', 'lib'))

    import logging


    from server.lib.config import *
    from server.lib.jobscript_builder import *
    from server.lib.scheduler import *
    from server.lib.manager import *


    #This is needed, otherwise no default logging happen
    logging.debug("Start test app")
    logger = logging.getLogger('RCM.composer')
    logger.setLevel(logging.INFO)

#    print("sys.argv",sys.argv[1:])

    list_paths = sys.argv[1:]
    #list_paths.append(os.path.join(os.environ.get('HOME',''), '.rcm', 'config', 'config.yaml'))                                CascadeYamlConfig.get()
    config = CascadeYamlConfig(list_paths = list_paths)

    manager = ServerManager()
    manager.init()
    print("####### manager.schedulers :", manager.schedulers)

    class_table = dict()
    plug_instances = dict()
    for scheduler in manager.schedulers:
        plug_instances[manager.schedulers[scheduler].NAME] = manager.schedulers[scheduler]
    class_table['SCHEDULER'] = (ConnectedManager, plug_instances)


    #SchedulerManager.register_scheduler([SlurmScheduler, PBSScheduler, LocalScheduler])
    root = AutoChoiceNode(name='TOP', schema=config.conf['schema'],
                                                    defaults=config.conf.get('defaults', None),
                                                    class_table=class_table)

    display_dialog_ui = root.get_gui_options()
    print(display_dialog_ui)
    def print_result(choices):
        print(json.dumps(choices, indent=4))
        res = root.substitute(choices)
        # SchedulerManager._allInstances[0].active_scheduler()
        for k, v in res.items():
            print(k, ":::>")
            print(v)

    display_dialog = QDisplayDialog(display_dialog_ui, callback=print_result)
    display_dialog.show()
    sys.exit(app.exec_())
