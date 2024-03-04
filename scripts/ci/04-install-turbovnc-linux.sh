#! /usr/bin/env bash

# Download 
wget "${TURBOVNC_DOWNLOAD:?}/${TURBOVNC_VERSION:?}/turbovnc_${TURBOVNC_VERSION:?}_amd64.deb" -O tmp/turbovnc.deb

# Extract
dpkg-deb -x tmp/turbovnc.deb tmp/turbovnc

# Copy extracted file to `"${TURBOVNC_EXTERNAL}"`
rm -rf "${TURBOVNC_EXTERNAL:?}"

cp -r tmp/turbovnc/opt/TurboVNC "${TURBOVNC_EXTERNAL:?}"
cp -r tmp/turbovnc/usr/share "${TURBOVNC_EXTERNAL:?}"
cp -r tmp/turbovnc/etc "${TURBOVNC_EXTERNAL:?}"