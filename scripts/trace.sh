#!/bin/bash
strace -f -t -e trace=file -e abbrev=all vncviewer 2>&1 |  cut -d'"' -f 2 | python trace.py 
