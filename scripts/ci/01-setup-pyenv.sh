#! /usr/bin/env bash
export PYENV_ROOT=.pyenv

if [ -n "${GITHUB_ENV}" ]; then
    echo "PYENV_ROOT=${PYENV_ROOT}" >> "${GITHUB_ENV}"
    echo "${PYENV_ROOT}/bin" >> "${GITHUB_PATH}"
    echo "${PYENV_ROOT}/versions/${PYTHON_VERSION}/bin" >> "${GITHUB_PATH}"
else
    export PYENV_ROOT="${PYENV_ROOT}"
    export PATH="${PYENV_ROOT}/bin:${PATH}"
    export PATH="${PYENV_ROOT}/versions/${PYTHON_VERSION}/bin:${PATH}"
fi