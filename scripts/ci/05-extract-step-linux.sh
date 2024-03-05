#! /usr/bin/env bash

# Download step
wget "${SMALLSTEP_DOWNLOAD:?}/v${SMALLSTEP_VERSION:?}/step_linux_${SMALLSTEP_VERSION:?}_amd64.tar.gz" -O "${RCM_CHECKOUT:?}/tmp/step.tgz"

# Make tmp and external directories
mkdir -p "${RCM_CHECKOUT:?}/${SMALLSTEP_EXTERNAL:?}"

# Extract and copy executable
tar -xzvf "${RCM_CHECKOUT:?}/tmp/step.tgz" -C "${RCM_CHECKOUT:?}/tmp"
cp "${RCM_CHECKOUT:?}"/tmp/step*/bin/step "${RCM_CHECKOUT:?}/${SMALLSTEP_EXTERNAL:?}"
