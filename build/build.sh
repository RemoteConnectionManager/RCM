#!/bin/bash

SCRIPT_PATH="${BASH_SOURCE[0]}";
if([ -h "${SCRIPT_PATH}" ]) then
  while([ -h "${SCRIPT_PATH}" ]) do SCRIPT_PATH=`readlink "${SCRIPT_PATH}"`; done
fi
pushd . > /dev/null
cd `dirname ${SCRIPT_PATH}` > /dev/null
SCRIPT_PATH=`pwd`;
popd  > /dev/null

rem cd %~dp0\pyinstaller-1.5.1
python ${SCRIPT_PATH}/../PyInstaller/pyinstaller-1.5.1/Build.py ${SCRIPT_PATH}/../spec_files/crv_client_tk.spec
