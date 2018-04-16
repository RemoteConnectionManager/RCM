#!/bin/bash
strace -f -t -e trace=file -e abbrev=all python /kubuntu/home/lcalori/spack/RCM/rcm/client/rcm_client_tk.py 2>&1 |  cut -d'"' -f 2 | python trace.py /tmp/dist 
