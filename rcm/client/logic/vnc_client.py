# std lib
import sys

# local includes
import client.logic.rcm_utils as rcm_utils
from client.miscellaneous.logger import logic_logger


class VNCClientCommandLineBuilder:
    def __init__(self):
        self.exe = ""
        self.command_line = ""

    def build(self):
        if  sys.platform == 'darwin':
            return
            
        exe = rcm_utils.which('vncviewer')
        if not exe :
            logic_logger.error("vncviewer not found! Check the PATH environment variable.")
            return
        if sys.platform == 'win32':
            # if the executable path contains spaces, it has to be put inside apexes
            exe = "\"" + exe + "\""
        self.exe = exe
        logic_logger.debug("vncviewer path: " + self.exe)

    def get_executable_path(self):
        return self.exe

    def get_command_line(self):
        return self.command_line
