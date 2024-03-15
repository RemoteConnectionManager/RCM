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

# CD in RCM directory
$env:RCM_CHECKOUT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

[regex]$Match1 = "^- "
$Replace1 = '$env:'
[regex]$Match2 = ": "
$Replace2 = " = "

foreach($line in Get-Content "${env:RCM_CHECKOUT}\scripts\ci\common_vars.yaml"){
    Invoke-Expression $Match2.replace($Match1.replace($line, $Replace1, 1), $Replace2, 1)
}

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
