$ErrorActionPreference = 'Stop'

# Create and activate venv
python.exe -m venv "${env:RCM_CHECKOUT}/.venv"
. "${env:RCM_CHECKOUT}\.venv\Scripts\Activate.ps1"

# Install packages
pip install -r "${env:RCM_CHECKOUT}\rcm\client\requirements.txt"

# Patch paramiko by downloading patch.exe and the pull-request commit
New-Item -ItemType Directory -Force -Path "${env:RCM_CHECKOUT}\tmp"

if (-Not (Get-Command "patch.exe" -ErrorAction SilentlyContinue)) {
    if ("${env:GITHUB_ENV}" -ne "") {
        $env:Path += ";C:\Program Files\Git\usr\bin"
    } else {

        New-Item -ItemType Directory -Force -Path "${env:RCM_CHECKOUT}\tmp\git"

        if (-Not (Test-Path "${env:RCM_CHECKOUT}\tmp\git\usr\bin\patch.exe")) {
            Invoke-WebRequest -URI "https://github.com/git-for-windows/git/releases/download/v2.44.0.windows.1/Git-2.44.0-32-bit.tar.bz2" -OutFile "${env:RCM_CHECKOUT}\tmp\git.tar.bz2" 
            tar.exe -xvf "${env:RCM_CHECKOUT}\tmp\git.tar.bz2" -C "${env:RCM_CHECKOUT}\tmp\git"
        }
        $env:Path += ";${env:RCM_CHECKOUT}\tmp\git\usr\bin"
    }
}

Invoke-WebRequest -URI "https://github.com/paramiko/paramiko/pull/${env:PARAMIKO_PULL}/commits/${env:PARAMIKO_COMMIT}.patch" -OutFile "${env:RCM_CHECKOUT}\tmp\paramiko.patch"
$env:PARAMIKO_DIR = python -c "import paramiko, os; print(os.path.dirname(paramiko.__file__))"
$env:PARAMIKO_FILE = "${env:PARAMIKO_DIR}\auth_handler.py"
patch.exe -N "${env:PARAMIKO_FILE}" -i "${env:RCM_CHECKOUT}\tmp\paramiko.patch"

$env:PARAMIKO_FILE = "${env:PARAMIKO_DIR}\pkey.py"
(Get-Content "${env:PARAMIKO_FILE}").replace("if 0x20 <= padding_length < 0x7F:", "if 0x20 <= padding_length < 0x7F or padding_length == 0:") | Set-Content "${env:PARAMIKO_FILE}"