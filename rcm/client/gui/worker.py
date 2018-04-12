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

    def __init__(self, display_name, rcm_client_connection):
        super().__init__()
        self.display_name = display_name
        self.rcm_client_connection = rcm_client_connection
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        print("Thread start")
        self.signals.status.emit(Status.PENDING)

        print("Polling the display job: " + str(self.display_name))

        connection = self.rcm_client_connection.newconn(queue='4core_18_gb_1h_slurm',
                                                        geometry='1200x1000',
                                                        sessionname = 'test',
                                                        vnc_id='fluxbox_turbovnc_vnc')

        newsession = connection.hash['sessionid']
        print("created session -->", newsession,
              "<- display->",
              connection.hash['display'],
              "<-- node-->",
              connection.hash['node'])
        self.rcm_client_connection.vncsession(connection)

        # time.sleep(5)
        self.signals.status.emit(Status.RUNNING)
        time.sleep(5)

        print("Thread complete")
        self.signals.status.emit(Status.FINISHED)
