#! /usr/bin/env bash

python -m venv "${RCM_CHECKOUT:?}/.venv"
source "${RCM_CHECKOUT:?}/.venv/bin/activate"
pip install -r "${RCM_CHECKOUT:?}/rcm/client/requirements.txt"

mkdir -p "${RCM_CHECKOUT:?}/tmp"
wget "https://github.com/paramiko/paramiko/pull/${PARAMIKO_PULL:?}/commits/${PARAMIKO_COMMIT:?}.patch" -O "${RCM_CHECKOUT:?}/tmp/paramiko.patch"
PARAMIKO_FILE=$(python -c "import paramiko, os; print(os.path.join(os.path.dirname(paramiko.__file__), 'auth_handler.py'))")
if [ -n "${GITHUB_ENV}" ]; then
    patch -N "${PARAMIKO_FILE}" -i "${RCM_CHECKOUT:?}/tmp/paramiko.patch"
else
    OUT="$(patch -N "${PARAMIKO_FILE}" -i "${RCM_CHECKOUT:?}/tmp/paramiko.patch")" || grep -q "Skipping patch" <<< "$OUT" || (echo "$OUT" && false)
fi
