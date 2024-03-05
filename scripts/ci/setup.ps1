$ErrorActionPreference = 'Stop'

$env:TURBOVNC_VERSION = '3.1'
$env:PYTHON_VERSION = "3.10.11"

# GENERIC
## pyenv
$env:PYENV_VERSION = "2.3.35"
## venv
$env:PARAMIKO_PULL = "2258"
$env:PARAMIKO_COMMIT = "1a45c7ec74cf8ee1d537e3ca032e7fef40fa62b3"
## turbovnc
$env:TURBOVNC_DOWNLOAD = "https://github.com/TurboVNC/turbovnc/releases/download"
$env:TURBOVNC_EXTERNAL = "rcm/client/external/turbovnc"
## patch turbovnc
$env:ORIG_LINE = 'jdk.tls.disabledAlgorithms=SSLv3, TLSv1, TLSv1.1, RC4, DES, MD5withRSA,'
$env:NEW_LINE = 'jdk.tls.disabledAlgorithms=SSLv3, RC4, DES, MD5withRSA,'
## smallstep
$env:SMALLSTEP_DOWNLOAD = "https://github.com/smallstep/cli/releases/download"
$env:SMALLSTEP_VERSION = "0.25.2"
$env:SMALLSTEP_EXTERNAL = "rcm/client/external/step"


# CD in RCM directory
$env:RCM_CHECKOUT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host "##############################################################################" -ForegroundColor Blue
Write-Host "# 1) SETUP ENVIRONMENT"  -ForegroundColor Blue
Write-Host "##############################################################################" -ForegroundColor Blue
. "${env:RCM_CHECKOUT}\scripts\ci\01-setup-pyenv.ps1"
Write-Host "Success" -ForegroundColor Green


Write-Host "##############################################################################" -ForegroundColor Blue
Write-Host "# 2) INSTALLING PYENV LOCALLY" -ForegroundColor Blue
Write-Host "##############################################################################" -ForegroundColor Blue
. "${env:RCM_CHECKOUT}\scripts\ci\02-install-python.ps1"
Write-Host "Success" -ForegroundColor Green


Write-Host "##############################################################################" -ForegroundColor Blue
Write-Host "# 3) INSTALLING VENV AND PATCH PARAMIKO" -ForegroundColor Blue
Write-Host "##############################################################################" -ForegroundColor Blue
. "${env:RCM_CHECKOUT}\scripts\ci\03-install-venv.ps1"
Write-Host "Success" -ForegroundColor Green


Write-Host "##############################################################################" -ForegroundColor Blue
Write-Host "# 4a) DOWNLOAD AND EXTRACT TURBOVNC" -ForegroundColor Blue
Write-Host "##############################################################################"  -ForegroundColor Blue
. "${env:RCM_CHECKOUT}\scripts\ci\04a-extract-turbovnc.ps1"
Write-Host "Success" -ForegroundColor Green


Write-Host "##############################################################################" -ForegroundColor Blue
Write-Host "# 4b) PATCH TURBOVNC" -ForegroundColor Blue
Write-Host "##############################################################################" -ForegroundColor Blue
. "${env:RCM_CHECKOUT}\scripts\ci\04b-patch-turbovnc.ps1"
Write-Host "Success" -ForegroundColor Green

Write-Host "##############################################################################" -ForegroundColor Blue
Write-Host "# 5) DOWNLOAD AND EXTRACT STEP" -ForegroundColor Blue
Write-Host "##############################################################################" -ForegroundColor Blue
. "${env:RCM_CHECKOUT}\scripts\ci\05-extract-step.ps1"
Write-Host "Success" -ForegroundColor Green

Write-Host "##############################################################################" -ForegroundColor Green
Write-Host "# ENVIRONMENT SETUP COMPLETED" -ForegroundColor Green
Write-Host "##############################################################################" -ForegroundColor Green

exit
