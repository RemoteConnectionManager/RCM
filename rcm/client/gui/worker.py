# std lib
import time
import traceback

# pyqt5
from PyQt5.QtCore import QRunnable, pyqtSlot, pyqtSignal, QObject

# local includes
from client.utils.rcm_enum import Status
from client.miscellaneous.logger import logger


# Reference https://martinfitzpatrick.name/article/multithreading-pyqt-applications-with-qthreadpool/


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.

    """

    status = pyqtSignal(Status)


class Worker(QRunnable):
    """
    Worker thread that polls the server to get the status
    of the job visualization task.

    """

    def __init__(self,
                 display_widget,
                 remote_connection_manager,
                 display_dlg):
        super().__init__()
        self.display_widget = display_widget
        self.display_id = display_widget.display_id
        self.remote_connection_manager = remote_connection_manager
        self.display_dlg = display_dlg
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            logger.debug("Worker for display " + str(self.display_id) + " started")
            self.signals.status.emit(Status.PENDING)

            version = self.remote_connection_manager.version()

            if version >= "1.0.0":
                display_session = self.remote_connection_manager.new(queue="dummy_queue",
                                                                     geometry="dummy_display_size",
                                                                     sessionname=self.display_id,
                                                                     vnc_id="dummy_vnc",
                                                                     choices=self.display_dlg.choices)
            else:
                display_session = self.remote_connection_manager.new(queue=self.display_dlg.session_queue,
                                                                     geometry=self.display_dlg.display_size,
                                                                     sessionname=self.display_id,
                                                                     vnc_id=self.display_dlg.session_vnc,
                                                                     choices=None)

            self.signals.status.emit(Status.RUNNING)

            self.display_widget.session = display_session
            self.remote_connection_manager.submit(display_session,
                                                  gui_cmd=self.display_widget.enable_connect_button)

            logger.debug("Worker for display " + str(self.display_id) + " finished")
        except Exception as e:
            logger.error("Exception: " + str(e) + " - " + str(traceback.format_exc()))
