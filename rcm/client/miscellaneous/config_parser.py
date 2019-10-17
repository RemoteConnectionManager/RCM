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

import os
from configparser import RawConfigParser

# local includes

config_file_name = os.path.join(os.path.expanduser('~'), '.rcm', 'rcm.cfg')
parser = RawConfigParser()

defaults = {
    'debug_log_level' : "false",
    'ssh_client' : '"internal"',
    'preload_command' : '"module load rcm; python $RCM_HOME/bin/server/rcm_new_server.py"'
}

preset_sessions = """
[
	    [
	        "@login.marconi.cineca.it",
	        "login.marconi.cineca.it",
	        "",
	        ""
	    ],
	    [
	        "@rcm.galileo.cineca.it",
	        "login.galileo.cineca.it",
	        "",
	        ""
	    ]
	]
"""

def merge_preset_sessions(curr_sessions,merge_sessions):
    to_append = []

    for merge_s in merge_sessions:
        append = True
        for curr_s in curr_sessions:
            if curr_s[1] == merge_s[1] and curr_s[3] == merge_s[3]:
                append =False
                break
        if append:
            to_append.append(merge_s)
    curr_sessions.extend(to_append)
    return curr_sessions

# parse config file to load the most recent sessions
if os.path.exists(config_file_name):
    try:
        with open(config_file_name, 'r') as config_file:
            parser.read_file(config_file, source=config_file_name)
    except Exception:
        print("Failed to load the config file")
else:
    print("Failed to load the config file: file does not exist")
