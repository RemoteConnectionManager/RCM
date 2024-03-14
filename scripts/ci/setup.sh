#! /usr/bin/env bash
set -e

usage() {
    cat >&1 <<EOF

Usage: $0 [--silent]
       $0 --restart [--silent]
       $0 --clean-only

Options:
  -u | --clean-only   : Clean actual setup without reinstalling it (python, venv, externals) [default: False]
  -r | --restart      : Restart installation without cleaning up [default: False]
  -s | --silent       : Suppress command stdout
  -h | --help         : Print usage message

EOF
}


options=$(getopt -o hscr --long help,silent,clean-only,restart -- "$@")
eval set -- "$options"
while true; do
    case "$1" in
    -h | --help) usage 0; exit 0;;
    -s | --silent) SILENT=1 && shift ;;
    -c | --clean-only) CLEAN_ONLY=1 && shift ;;
    -r | --restart) RESTART=1 && shift ;;
    --) shift && break ;;
    *) usage ;;
    esac
done

if [[ "${CLEAN_ONLY}" -eq 1 ]] && [[ "${RESTART}" -eq 1 ]]; then
    printf "\033[1;31m%s\033[0m\n" "Error: '--clean-only' and '--restart' cannot be use at the same time." 1>&2
    exit 1
fi

SEPARATOR="##############################################################################"
function run_step {
    TITLE=$1
    SCRIPT=$2
    TARGET_DIR=$3

    printf '\033[1;34m%s\n# %s\n%s\033[0m\n' "${SEPARATOR}" "${TITLE}" "${SEPARATOR}"

    if [ -n "${SCRIPT}" ]; then
        if [[ "${RESTART}" -ne 1 ]] && [[ -d "${TARGET_DIR}" ]]; then
            printf "\e[90m[INFO] Removing '%s' dir ...\033[0m\n" "${TARGET_DIR}"
            rm -rf "${TARGET_DIR}"
        fi
        if [[ "${CLEAN_ONLY}" -ne 1 ]]; then
            printf "\e[90m[INFO] Running '%s' ...\033[0m\n" "${SCRIPT}"
            if [[ "${SILENT}" -eq 1 ]]; then
                "${SCRIPT}" > /dev/null
            else
                "${SCRIPT}"
            fi
        fi
        echo -e "\033[0;32mSuccess\033[0m"
    fi
}

export TURBOVNC_VERSION='3.1'
export PYTHON_VERSION="3.10.11"

# GENERIC
## pyenv
export PYENV_VERSION="2.3.35"
## venv
export PARAMIKO_PULL="2258"
export PARAMIKO_COMMIT="1a45c7ec74cf8ee1d537e3ca032e7fef40fa62b3"
## turbovnc
export TURBOVNC_DOWNLOAD="https://github.com/TurboVNC/turbovnc/releases/download"
export TURBOVNC_EXTERNAL="rcm/client/external/turbovnc"
## patch turbovnc
export ORIG_LINE='jdk.tls.disabledAlgorithms=SSLv3, TLSv1, TLSv1.1, RC4, DES, MD5withRSA,'
export NEW_LINE='jdk.tls.disabledAlgorithms=SSLv3, RC4, DES, MD5withRSA,'
## smallstep
export SMALLSTEP_DOWNLOAD="https://github.com/smallstep/cli/releases/download"
export SMALLSTEP_VERSION="0.25.2"
export SMALLSTEP_EXTERNAL="rcm/client/external/step"


# CD in RCM directory
RCM_CHECKOUT="$(dirname "$0")/../../"
export RCM_CHECKOUT

run_step "1) SETUP ENVIRONMENT" \
         "${RCM_CHECKOUT}/scripts/ci/01-setup-pyenv.sh" \
         "${RCM_CHECKOUT}/tmp"

run_step "2) INSTALLING PYENV LOCALLY" \
         "${RCM_CHECKOUT}/scripts/ci/02-install-python.sh" \
         "${RCM_CHECKOUT}/.pyenv" 

run_step "3) INSTALLING VENV AND PATCH PARAMIKO" \
         "${RCM_CHECKOUT}/scripts/ci/03-install-venv.sh" \
         "${RCM_CHECKOUT}/.venv" 

run_step "4a) DOWNLOAD AND EXTRACT TURBOVNC" \
         "${RCM_CHECKOUT}/scripts/ci/04a-extract-turbovnc-ubuntu.sh" \
         "${RCM_CHECKOUT}/rcm/client/external/turbovnc" 

run_step "4b) INSTALLING PYENV LOCALLY" \
         "${RCM_CHECKOUT}/scripts/ci/04b-patch-turbovnc-linux.sh"

run_step "5) DOWNLOAD AND EXTRACT STEP" \
         "${RCM_CHECKOUT}/scripts/ci/05-extract-step-linux.sh" \
         "${RCM_CHECKOUT}/rcm/client/external/step" 

printf '\033[0;32mm%s\n# %s\n%s\033[0m\n' "${SEPARATOR}" "ENVIRONMENT SETUP COMPLETED" "${SEPARATOR}"
