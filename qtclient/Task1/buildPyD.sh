#!/bin/bash
ONEFILE_PATH="pythonHelloWorld/dist_onDir"
source ../py3env/bin/activate
if [ -d $ONEFILE_PATH ]; then
	rm -rf $ONEFILE_PATH
fi
pyinstaller -D --distpath $ONEFILE_PATH --workpath pythonHelloWorld/build_oneDir --specpath pythonHelloWorld/ pythonHelloWorld/helloworld.py
sleep 1
