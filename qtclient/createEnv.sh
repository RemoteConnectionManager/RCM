#!/bin/bash
#creo Environment py3env, se virtualenv non è installato, lo installa
if ! which virtualenv > /dev/null; then
      sudo apt-get install virtualenv
fi
if [ ! -d "py3env" ]; then
	virtualenv -p python3 py3env
fi
source ./py3env/bin/activate
#installa pyqt5 e pyinstaller
pip install PyQt5
pip install pyinstaller
