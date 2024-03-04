#! /usr/bin/env bash

# Download step
wget "${SMALLSTEP_DOWNLOAD:?}/v${SMALLSTEP_VERSION:?}/step_linux_${SMALLSTEP_VERSION:?}_amd64.tar.gz" -O tmp/step.tgz

# Make tmp and external directories
mkdir -p "${SMALLSTEP_EXTERNAL:?}"

# Extract and copy executable
tar -xzvf tmp/step.tgz -C tmp
cp tmp/step*/bin/step "${SMALLSTEP_EXTERNAL:?}"

# Check
ls "${SMALLSTEP_EXTERNAL:?}"