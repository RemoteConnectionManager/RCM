#! /usr/bin/env bash
set -e

usage() {
    EXIT_CODE=$1
    if [[ $EXIT_CODE -ge 1 ]]; then
        STD=2
    else
        STD=1
    fi
    SCRIPT_NAME=$(basename $0)
    cat >&$STD <<EOF
Setup linux environment for RCM development.

Usage: $SCRIPT_NAME [--restart|--clean-only]

Options:
  -c, --clean-only  clean actual enviroment without reinstalling it [default: False]
  -r, --restart     restart installation without cleaning up [default: False]
  -h, --help        display this help and exit
EOF
    exit $EXIT_CODE
}


options=$(getopt -o hscr --long help,silent,clean-only,restart -- "$@")
eval set -- "$options"
while true; do
    case "$1" in
    -h | --help) usage 0;;
    -c | --clean-only) CLEAN_ONLY=1 && shift ;;
    -r | --restart) RESTART=1 && shift ;;
    --) shift && break ;;
    *) usage 1;;
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
            . "${SCRIPT}"
        fi
        echo -e "\033[0;32mSuccess\033[0m"
    fi
}


# CD in RCM directory
RCM_CHECKOUT="$(realpath $(dirname "$0")/../..)"
export RCM_CHECKOUT

eval "$(sed 's/- /export /;s/: /=/' "${RCM_CHECKOUT}/scripts/ci/common_vars.yaml")"

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

run_step "4b) PATH TURBOVNC 3.x JAVA CONF" \
         "${RCM_CHECKOUT}/scripts/ci/04b-patch-turbovnc-linux.sh"

run_step "5) DOWNLOAD AND EXTRACT STEP" \
         "${RCM_CHECKOUT}/scripts/ci/05-extract-step-linux.sh" \
         "${RCM_CHECKOUT}/rcm/client/external/step" 

printf '\033[0;32mm%s\n# %s\n%s\033[0m\n' "${SEPARATOR}" "ENVIRONMENT SETUP COMPLETED" "${SEPARATOR}"
