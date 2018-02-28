#!/bin/bash
ONEFILE_PATH="pythonHelloWorld/dist_oneFile"
source ../py3env/bin/activate
if [ -d $ONEFILE_PATH ]; then
	rm -rf $ONEFILE_PATH
fi
pyinstaller -F --distpath $ONEFILE_PATH --workpath pythonHelloWorld/build_oneFile --specpath pythonHelloWorld/ pythonHelloWorld/helloworld.py
sleep 1
