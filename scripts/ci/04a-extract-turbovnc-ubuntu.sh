#! /usr/bin/env bash

mkdir -p "${RCM_CHECKOUT:?}/tmp/turbovnc"

# Download
wget "${TURBOVNC_DOWNLOAD:?}/${TURBOVNC_VERSION:?}/turbovnc_${TURBOVNC_VERSION:?}_amd64.deb" -O "${RCM_CHECKOUT:?}/tmp/turbovnc.deb"

# Extract without using dpkg-deb that is distributed only in debian-based distro
# dpkg-deb -x "${RCM_CHECKOUT:?}/tmp/turbovnc.deb" "${RCM_CHECKOUT:?}/tmp/turbovnc"
ar -x "${RCM_CHECKOUT:?}/tmp/turbovnc.deb" --output "${RCM_CHECKOUT:?}/tmp"
tar -xvf "${RCM_CHECKOUT:?}/tmp/data.tar.xz" -C "${RCM_CHECKOUT:?}/tmp/turbovnc"

# Copy extracted file to `"${TURBOVNC_EXTERNAL}"`
rm -rf "${RCM_CHECKOUT:?}/${TURBOVNC_EXTERNAL:?}"

cp -r "${RCM_CHECKOUT:?}/tmp/turbovnc/opt/TurboVNC" "${RCM_CHECKOUT:?}/${TURBOVNC_EXTERNAL:?}"
cp -r "${RCM_CHECKOUT:?}/tmp/turbovnc/usr/share" "${RCM_CHECKOUT:?}/${TURBOVNC_EXTERNAL:?}"
cp -r "${RCM_CHECKOUT:?}/tmp/turbovnc/etc" "${RCM_CHECKOUT:?}/${TURBOVNC_EXTERNAL:?}"
