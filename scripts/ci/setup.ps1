param(
    [Parameter(HelpMessage="Clean actual setup without reinstalling it (python, venv, externals) [default: False]")]
    [switch]$CleanOnly,

    [Parameter(HelpMessage="Restart installation without cleaning up [default: False]")]
    [switch]$Restart
)

$ErrorActionPreference = 'Stop'

if ($CleanOnly -and $Restart) {
    Write-Error "Error: '-CleanOnly' and '-Restart' cannot be use at the same time."
    exit 1
}

$SEPARATOR = "#"*79

function RunStep {

    param (
        [Parameter(Mandatory=$true, HelpMessage="Step title")]
        [string]$Title,
        
        [Parameter(HelpMessage="Script to run")]
        [string]$Script,

        [Parameter(HelpMessage="Target dir to eventually clean")]
        [string]$TargetDir
    )
    Write-Host ("{0}`n# {1}`n{0}" -f "${SEPARATOR}", "${Title}" ) -ForegroundColor Blue

    if ($PSBoundParameters.ContainsKey('Script')) {
        if (-Not ${Restart} -and $PSBoundParameters.ContainsKey('TargetDir') -and (test-path $TargetDir)){
            Write-Host "[INFO] Removing '${TargetDir}' dir ..." -ForegroundColor DarkGray
            Remove-Item "${TargetDir}" -Force -Recurse
        }
        if ( -Not ${CleanOnly} ) {
            Write-Host "[INFO] Running '${Script}' ..."  -ForegroundColor DarkGray
            . "${Script}"
        }
        Write-Host "Success" -ForegroundColor Green
    }
}


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

RunStep -Title "1) SETUP ENVIRONMENT" `
        -Script "${env:RCM_CHECKOUT}\scripts\ci\01-setup-pyenv.ps1" `
        -TargetDir "${env:RCM_CHECKOUT}\tmp"

RunStep -Title "2) INSTALLING PYENV LOCALLY" `
        -Script "${env:RCM_CHECKOUT}\scripts\ci\02-install-python.ps1" `
        -TargetDir "${env:RCM_CHECKOUT}\.pyenv" 

RunStep -Title "3) INSTALLING VENV AND PATCH PARAMIKO" `
        -Script "${env:RCM_CHECKOUT}\scripts\ci\03-install-venv.ps1" `
        -TargetDir "${env:RCM_CHECKOUT}\.venv" 

RunStep -Title "4a) DOWNLOAD AND EXTRACT TURBOVNC" `
        -Script "${env:RCM_CHECKOUT}\scripts\ci\04a-extract-turbovnc.ps1" `
        -TargetDir "${env:RCM_CHECKOUT}\rcm\client\external\turbovnc" 

RunStep -Title "4b) INSTALLING PYENV LOCALLY" `
        -Script "${env:RCM_CHECKOUT}\scripts\ci\04b-patch-turbovnc.ps1"

RunStep -Title "5) DOWNLOAD AND EXTRACT STEP" `
        -Script "${env:RCM_CHECKOUT}\scripts\ci\05-extract-step.ps1" `
        -TargetDir "${env:RCM_CHECKOUT}\rcm\client\external\step" 

Write-Host ("{0}`n# {1}`n{0}" -f "${SEPARATOR}", "ENVIRONMENT SETUP COMPLETED" ) -ForegroundColor Green
