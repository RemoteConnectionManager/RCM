#! /usr/bin/env bash
set -e

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
cd "$(dirname "$0")/../../"

if uname -a | grep -q "^Linux"; then
    echo -e "\033[0;34m##############################################################################"
    echo -e "# 0) INSTALLING QT5 DEPENDENCIES \033[0;31m(SUDO IS REQUIRED)\033[0;34m"
    echo -e "##############################################################################\033[0m"
    sudo apt update
    sudo apt install qtbase5-dev qt5-qmake qtwayland5
    echo -e "\033[0;32mSuccess\033[0m"

fi

echo -e "\033[0;34m##############################################################################"
echo -e "# 1) SETUP PYENV ENVIRONMENT"
echo -e "##############################################################################\033[0m"
source "scripts/ci/01-setup-pyenv.sh"
echo -e "\033[0;32mSuccess\033[0m"

echo -e "\033[0;34m##############################################################################"
echo -e "# 2) INSTALLING PYENV LOCALLY"
echo -e "##############################################################################\033[0m"
. "scripts/ci/02-install-python.sh"
echo -e "\033[0;32mSuccess\033[0m"

echo -e "\033[0;34m##############################################################################"
echo -e "# 3) INSTALLING VENV AND PATCH PARAMIKO"
echo -e "##############################################################################\033[0m"
. "scripts/ci/03-install-venv.sh"
echo -e "\033[0;32mSuccess\033[0m"

if uname -a | grep -q "^Linux"; then
    echo -e "\033[0;34m##############################################################################"
    echo -e "# 4) DOWNLOAD AND EXTRACT TURBOVNC (LINUX-ONLY)"
    echo -e "##############################################################################\033[0m"
    . "scripts/ci/04-install-turbovnc-linux.sh"
    echo -e "\033[0;32mSuccess\033[0m"

    echo -e "\033[0;34m##############################################################################"
    echo -e "# 5) PATCH TURBOVNC (LINUX-ONLY)"
    echo -e "##############################################################################\033[0m"
    . "scripts/ci/05-patch-turbovnc-linux.sh"
    echo -e "\033[0;32mSuccess\033[0m"

    echo -e "\033[0;34m##############################################################################"
    echo -e "# 6) DOWNLOAD AND EXTRACT STEP (LINUX-ONLY)"
    echo -e "##############################################################################\033[0m"
    . "scripts/ci/06-install-step-linux.sh"
    echo -e "\033[0;32mSuccess\033[0m"
fi

echo -e "\033[0;32m##############################################################################"
echo -e "# ENVIRONMENT SETUP COMPLETED"
echo -e "##############################################################################\033[0m"
