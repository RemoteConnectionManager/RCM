$ErrorActionPreference = "Stop"

if (Test-Path -Path .\venv ) {
    Remove-Item .\venv -Recurse -Force
}

python\python.exe -m venv venv
venv\Scripts\Activate.ps1
pip install -r RCM\rcm\client\requirements.txt