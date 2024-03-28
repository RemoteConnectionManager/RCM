#!/bin/env python
#
# Copyright (c) 2014-2019 CINECA.
#
# This file is part of RCM (Remote Connection Manager) 
# (see http://www.hpc.cineca.it/software/rcm).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

# std lib
import os
import sys
import socket
import shutil
import hashlib
import urllib.request
root_rcm_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_rcm_path)

# local includes
from rcm.client.miscellaneous.logger import logic_logger
import rcm.client.utils.pyinstaller_utils as pyinstaller_utils


def compute_checksum(filename):
    fh = open(filename, 'rb')
    m = hashlib.md5()
    while True:
        data = fh.read(8192)
        if not data:
            break
        m.update(data)
    return m.hexdigest()


def download_file(url, outfile):
    req_info = urllib.request.urlopen(url)
    file_size = int(req_info.headers['Content-Length'])
    with open(outfile, 'wb') as f:
        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = req_info.read(block_sz)
            if not buffer:
                break
            file_size_dl += len(buffer)
            f.write(buffer)
            p = float(file_size_dl) / file_size


def which(*args, **kwargs):
    """Finds an executable in the path like command-line which.

    If given multiple executables, returns the first one that is found.
    If no executables are found, returns None.

    Parameters:
        *args (str): One or more executables to search for

    Keyword Arguments:
        path (:func:`list` or str): The path to search. Defaults to ``PATH``
        required (bool): If set to True, raise an error if executable not found

    Returns:
        Executable: The first executable that is found in the path
    """
    from six import string_types
    path = kwargs.get('path', os.environ.get('PATH', ''))
    required = kwargs.get('required', False)

    if isinstance(path, string_types):
        path = path.split(os.pathsep)

    for name in args:
        for directory in path:
            exe = os.path.join(directory, name)
            if sys.platform == 'win32':
                rexe = exe + '.exe'
                if os.path.isfile(rexe):
                    return rexe
                else:
                    rbat = exe + '.bat'
                    if os.path.isfile(rbat):
                        return rbat

            else:
                if os.path.isfile(exe) and os.access(exe, os.X_OK):
                    return exe
    print("File: " + name + " NOT FOUND in " + str(path))
    return None


def client_folder():
    return os.path.join(os.path.expanduser('~'), '.rcm')


def log_folder():
    return os.path.join(client_folder(), 'logs')


def copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        logic_logger.debug("Creating folder " + dst)
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            if not os.path.exists(d):
                logic_logger.debug("Copy: " + s + " >> " + d)
                shutil.copy2(s, d)
            else:
                source_hash = compute_checksum(s)
                dest_hash = compute_checksum(d)
                if source_hash == dest_hash:
                    logic_logger.debug("Found previous: " + d)
                else:
                    logic_logger.warning("Update previous: " + s + " >> " + d)
                    shutil.copy2(s, d)


# this is the real class, hidden
class _pack_info:
    def __init__(self):
        # Read file containing the platform on which the client were build
        build_platform_filename = pyinstaller_utils.resource_path("build_platform.txt")

        self.buildPlatformString = ""
        self.rcmVersion = ""
        self.checksumString = ""
        self.client_info = {}

        if os.path.exists(build_platform_filename):
            logic_logger.debug("Reading build platform file " + build_platform_filename)
            with open(build_platform_filename, "r") as f:
                self.buildPlatformString = f.readline().strip()
                self.rcmVersion = f.readline()
                logic_logger.debug("buildPlatformString: " + self.buildPlatformString)
                logic_logger.debug("rcmVersion: " + self.rcmVersion)

        if pyinstaller_utils.is_bundled():
            self.checksumString = str(compute_checksum(sys.executable))

    def add_client_screen_dimensions(self,x,y):
        self.client_info['screen_width'] = x
        self.client_info['screen_height'] = y

    def to_dict(self):
        return {'platform': self.buildPlatformString,
                'version': self.rcmVersion,
                'checksum': self.checksumString,
                'client_info': self.client_info}


# pack_info is a kind of singleton, this is the only instance
_pack_info_instance = None

def pack_info():
    global _pack_info_instance
    if  _pack_info_instance is None:

        _pack_info_instance = _pack_info()
    return _pack_info_instance


def get_unused_portnumber():
    sock = socket.socket()
    sock.bind(('', 0))
    sn=sock.getsockname()[1]
    sock.close()
    return sn
