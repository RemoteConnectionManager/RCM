#! /usr/bin/env bash

JAVA_SECURITY=$(find "${RCM_CHECKOUT:?}/${TURBOVNC_EXTERNAL:?}" -name java.security)
sed -i "s/${ORIG_LINE:?}/${NEW_LINE:?}/" "${JAVA_SECURITY}"