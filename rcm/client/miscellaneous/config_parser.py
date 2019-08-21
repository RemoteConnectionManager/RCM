# std lib
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
	        "@login.galileo.cineca.it?dev",
	        "login.galileo.cineca.it",
	        "",
	        "module unuse /galileo/prod/spack/v001/RCM_spack_deploy/deploy/galileo_dev00/insitu01/spack/share/spack/modules/linux-centos7-x86_64; module unuse /galileo/home/userinternal/lcalori0/spack/RCM_spack_deploy/deploy/rcm_chained/modules/linux-centos7-x86_64;  module use --prepend  /galileo/prod/spack/v001/RCM_spack_deploy/deploy/galileo_dev00/insitu01/spack/share/spack/modules/linux-centos7-x86_64 /galileo/home/userinternal/lcalori0/spack/RCM_spack_deploy/deploy/base_spack_devel/modules/linux-centos7-x86_64 /galileo/home/userinternal/lcalori0/spack/RCM_spack_deploy/deploy/rcm_chained/modules/linux-centos7-x86_64;   export RCM_CONFIG_BASE_PATH=test/etc/test_hierarchical; export RCM_CONFIG_PATHS='base_scheduler:base_service:slurm_gres:network:other:logging/debug/api.yaml'; module load rcm; python $RCM_HOME/src/rcm/server/bin/server",
	    ],
	    [
	        "@login.marconi.cineca.it",
	        "login.marconi.cineca.it",
	        "",
	        ""
	    ],
	    [
	        "@login.galileo.cineca.it",
	        "login.galileo.cineca.it",
	        "",
	        ""
	    ],
	    [
	        "@login04.galileo.cineca.it?interactiveGPU",
	        "login04.galileo.cineca.it",
	        "",
	        "module use /galileo/prod/spack/v001/RCM_spack_deploy/deploy/galileo_dev00/insitu01/spack/share/spack/modules/linux-centos7-x86_64; "
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
