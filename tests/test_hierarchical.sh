#!/bin/bash

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
# resolve $SOURCE until the file is no longer a symli nk
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" 
# if $SOURCE was a relative symli nk, 
# we need to resolve it relative to the path where the symlink file was located
done

export CURRPATH="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

echo "--------$CURRPATH ---------"

export PATH=$PATH:${CURRPATH}/fake_slurm
python ${CURRPATH}/../rcm/client/gui/new_display_dialog.py test_hierarchical/slurm_gres test_hierarchical/base_scheduler test_hierarchical/base_service
