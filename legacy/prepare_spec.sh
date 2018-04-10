#/bin/bash

VNCVIEWER_ABS=$(which vncviewer)
VNCVIEWER_REL=$(python -c "import sys,platform; print 'external/'+sys.platform+'/'+platform.architecture()[0]+'/bin'")
VNCVIEWER_OPT="--add-binary ${VNCVIEWER_ABS}:${VNCVIEWER_REL}"

JAVA_ABS=$(which java)
JAVA_REL=$(python -c "import sys,platform; print 'external/'+sys.platform+'/'+platform.architecture()[0]+'/bin'")
JAVA_OPT="--add-binary ${JAVA_ABS}:${JAVA_REL}"

COMMAND_BASE="pyi-makespec"
COMMAND_BASE="pyinstaller --distpath=/tmp/paperino"

MAKESPEC_BASE="${COMMAND_BASE} --specpath spec_files --hidden-import rcm --paths . --paths server --paths client ${VNCVIEWER_OPT} ${JAVA_OPT}"

MAKESPEC_COMMAND="${MAKESPEC_BASE} --name RCM_dir --onedir $@"
echo "One_dir command-->${MAKESPEC_COMMAND}<--"
${MAKESPEC_COMMAND}

MAKESPEC_COMMAND="${MAKESPEC_BASE} --name RCM_file --onefile $@"
echo "One_file command-->${MAKESPEC_COMMAND}<--"
${MAKESPEC_COMMAND} 
