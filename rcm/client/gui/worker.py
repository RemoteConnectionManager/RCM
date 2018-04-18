# std lib
import time

# pyqt5
from PyQt5.QtCore import QRunnable, pyqtSlot, pyqtSignal, QObject

# local includes
from client.utils.rcm_enum import Status


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
                 session_queue,
                 session_vnc,
                 display_size):
        super().__init__()
        self.display_widget = display_widget
        self.display_id = display_widget.display_id
        self.remote_connection_manager = remote_connection_manager
        self.session_queue = session_queue
        self.session_vnc = session_vnc
        self.display_size = display_size
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        print("Thread start")
        self.signals.status.emit(Status.PENDING)

        display_session = self.remote_connection_manager.newconn(queue=self.session_queue,
                                                                 geometry=self.display_size,
                                                                 sessionname=self.display_id,
                                                                 vnc_id=self.session_vnc)

        self.display_widget.session = display_session
        self.remote_connection_manager.vncsession(display_session)

        self.signals.status.emit(Status.RUNNING)
        print("Thread complete")
