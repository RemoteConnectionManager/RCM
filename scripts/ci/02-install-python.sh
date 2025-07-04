#! /usr/bin/env bash

if [ ! -d "${PYENV_ROOT:?}" ]; then
    git clone -b "v${PYENV_VERSION:?}" "https://github.com/pyenv/pyenv.git" "${PYENV_ROOT:?}"
fi

# https://github.com/pyenv/pyenv/issues/3211
if [[ $( sw_vers -productVersion 2>/dev/null ) ==  15.* ]]; then
    export PYTHON_BUILD_HOMEBREW_OPENSSL_FORMULA="openssl@3"
fi

pyenv install -s "${PYTHON_VERSION:?}"
