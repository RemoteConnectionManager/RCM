#! /usr/bin/env bash

if [ ! -d "${PYENV_ROOT:?}" ]; then
    git clone -b "v${PYENV_VERSION:?}" "https://github.com/pyenv/pyenv.git" "${PYENV_ROOT:?}"
fi
pyenv install -s "${PYTHON_VERSION:?}"