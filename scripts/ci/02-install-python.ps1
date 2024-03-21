$ErrorActionPreference = 'Stop'

# Clone pyenv-win if missing
if (-Not (Test-Path "${env:PYENV_ROOT}")) {
    git clone "https://github.com/pyenv-win/pyenv-win.git" (Split-Path -Parent "$env:PYENV_ROOT")
}
# Install python
pyenv.bat install -s "${env:PYTHON_VERSION}"