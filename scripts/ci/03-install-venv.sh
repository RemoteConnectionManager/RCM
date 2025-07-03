#! /usr/bin/env bash

python -m venv "${RCM_CHECKOUT:?}/.venv"
source "${RCM_CHECKOUT:?}/.venv/bin/activate"
pip install -r "${RCM_CHECKOUT:?}/rcm/client/requirements.txt"

mkdir -p "${RCM_CHECKOUT:?}/tmp"
wget "https://github.com/paramiko/paramiko/pull/${PARAMIKO_PULL:?}/commits/${PARAMIKO_COMMIT:?}.patch" -O "${RCM_CHECKOUT:?}/tmp/paramiko.patch"

PARAMIKO_DIR=$(python -c "import paramiko, os; print(os.path.dirname(paramiko.__file__))")
PARAMIKO_FILE="${PARAMIKO_DIR}"/auth_handler.py
if [ -n "${GITHUB_ENV}" ]; then
    patch -N "${PARAMIKO_FILE}" -i "${RCM_CHECKOUT:?}/tmp/paramiko.patch"
else
    OUT="$(patch -N "${PARAMIKO_FILE}" -i "${RCM_CHECKOUT:?}/tmp/paramiko.patch")" || grep -q "Skipping patch" <<< "$OUT" || (echo "$OUT" && false)
fi

PARAMIKO_FILE="${PARAMIKO_DIR}"/pkey.py
sed -i.backup "s/if 0x20 <= padding_length < 0x7F:/if 0x20 <= padding_length < 0x7F or padding_length == 0:/" "${PARAMIKO_FILE}"
