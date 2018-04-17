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

    def __init__(self, display_id, remote_connection_manager):
        super().__init__()
        self.display_id = display_id
        self.remote_connection_manager = remote_connection_manager
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        print("Thread start")
        self.signals.status.emit(Status.PENDING)

        connection = self.remote_connection_manager.newconn(queue='4core_18_gb_1h_slurm',
                                                        geometry='1200x1000',
                                                        sessionname = self.display_id,
                                                        vnc_id='fluxbox_turbovnc_vnc')

        newsession = connection.hash['sessionid']
        print("created session -->", newsession,
              "<- display->",
              connection.hash['display'],
              "<-- node-->",
              connection.hash['node'])
        self.remote_connection_manager.vncsession(connection)

        self.signals.status.emit(Status.RUNNING)
        print("Thread complete")
