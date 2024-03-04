#! /usr/bin/env bash

python -m venv .venv
source .venv/bin/activate
pip install -r "rcm/client/requirements.txt"

mkdir -p tmp
wget "https://github.com/paramiko/paramiko/pull/${PARAMIKO_PULL:?}/commits/${PARAMIKO_COMMIT:?}.patch" -O tmp/paramiko.patch
PARAMIKO_FILE=$(python -c "import paramiko, os; print(os.path.join(os.path.dirname(paramiko.__file__), 'auth_handler.py'))")
if [ -n "${GITHUB_ENV}" ]; then
    patch -N "${PARAMIKO_FILE}" -i tmp/paramiko.patch
else
    OUT="$(patch -N "${PARAMIKO_FILE}" -i tmp/paramiko.patch)" || grep -q "Skipping patch" <<< "$OUT" || (echo "$OUT" && false)
fi
