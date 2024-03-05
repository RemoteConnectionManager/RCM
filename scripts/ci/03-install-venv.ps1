$ErrorActionPreference = 'Stop'

# Create and activate venv
python.exe -m venv "${env:RCM_CHECKOUT}/.venv"
. "${env:RCM_CHECKOUT}\.venv\Scripts\Activate.ps1"

# Install packages
pip install -r "${env:RCM_CHECKOUT}\rcm\client\requirements.txt"

# Patch paramiko by downloading patch.exe and the pull-request commit
New-Item -ItemType Directory -Force -Path "${env:RCM_CHECKOUT}\tmp"
New-Item -ItemType Directory -Force -Path "${env:RCM_CHECKOUT}\tmp\git"

if (-Not (Test-Path "${env:RCM_CHECKOUT}\tmp\git\usr\bin\patch.exe")) {
    Invoke-WebRequest -URI "https://github.com/git-for-windows/git/releases/download/v2.44.0.windows.1/Git-2.44.0-32-bit.tar.bz2" -OutFile "${env:RCM_CHECKOUT}\tmp\git.tar.bz2" 
    tar.exe -xvf "${env:RCM_CHECKOUT}\tmp\git.tar.bz2" -C "${env:RCM_CHECKOUT}\tmp\git"
}

Invoke-WebRequest -URI "https://github.com/paramiko/paramiko/pull/${env:PARAMIKO_PULL}/commits/${env:PARAMIKO_COMMIT}.patch" -OutFile "${env:RCM_CHECKOUT}\tmp\paramiko.patch"
$env:PARAMIKO_FILE = python -c "import paramiko, os; print(os.path.join(os.path.dirname(paramiko.__file__), 'auth_handler.py'))"
. "${env:RCM_CHECKOUT}\tmp\git\usr\bin\patch.exe" -s -N "${env:PARAMIKO_FILE}" -i "${env:RCM_CHECKOUT}\tmp\paramiko.patch"
