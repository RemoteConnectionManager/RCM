param
(
    [string]$PYTHON_VERSION = $env:PYTHON_VERSION
)
    
$ErrorActionPreference = "Stop"

if ($PYTHON_VERSION -eq '') {
    throw "PYTHON_VERSION has not been passed or set in the environment"
}


if (Test-Path -Path .\.pyenv ) {
    Remove-Item .\.pyenv\ -Recurse -Force
}
git clone "https://github.com/pyenv-win/pyenv-win.git" .pyenv

.\.pyenv\pyenv-win\bin\pyenv.bat install ${PYTHON_VERSION}

#############################################
# TO BE REMOVED IF ARTIFACT ARE NOT REQUIRED
#############################################
if (Test-Path -Path .\python ) {
    Remove-Item .\python -Recurse -Force
}

Move-Item .pyenv\pyenv-win\versions\${PYTHON_VERSION} python
Get-ChildItem python
#############################################

python\python.exe --version

