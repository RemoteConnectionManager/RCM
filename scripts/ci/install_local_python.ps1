Set-StrictMode -Version Latest

git clone "https://github.com/pyenv-win/pyenv-win.git" .pyenv
.\.pyenv\pyenv-win\bin\pyenv.bat install ${env:PYTHON_VERSION}

#############################################
# TO BE REMOVED IF ARTIFACT ARE NOT REQUIRED
#############################################
mv .pyenv\pyenv-win\versions\${env:PYTHON_VERSION} python
ls python
#############################################

python\python.exe --version

