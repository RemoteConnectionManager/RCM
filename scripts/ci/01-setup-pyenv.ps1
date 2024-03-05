$ErrorActionPreference = 'Stop'

# Define pyenv-win root
$env:PYENV_ROOT = "${env:RCM_CHECKOUT}\.pyenv\pyenv-win"

# Define other variables and add pyenv and python in PATH
if ("${env:GITHUB_ENV}" -ne "") {
    # GitHub way to permanentely set and modify variables
    Write-Output "PYENV=${env:PYENV_ROOT}\" >> "${env:GITHUB_ENV}"
    Write-Output "PYENV_ROOT=${env:PYENV_ROOT}\" >> "${env:GITHUB_ENV}"
    Write-Output "PYENV_HOME=${env:PYENV_ROOT}\" >> "${env:GITHUB_ENV}"

    Write-Output "${env:PYENV_ROOT}\bin" >> "${env:GITHUB_PATH}"
    Write-Output "${env:PYENV_ROOT}\shims" >> "${env:GITHUB_PATH}"
    Write-Output "${env:PYENV_ROOT}\versions\${env:PYTHON_VERSION}" >> "${env:GITHUB_PATH}"

    Write-Output "C:\Program Files\Git\usr\bin" >> "${env:GITHUB_PATH}"
} else {
    # GitHub way to permanentely set and modify variables
    $env:PYENV = "${env:PYENV_ROOT}\"
    $env:PYENV_HOME = "${env:PYENV_ROOT}\"

    $env:PATH = "${env:PYENV_ROOT}\bin;${env:PATH}"
    $env:PATH = "${env:PYENV_ROOT}\shims;${env:PATH}"
    $env:PATH = "${env:PYENV_ROOT}\versions\${env:PYTHON_VERSION};${env:PATH}"
}
