#!/bin/bash
if [ -f $CRV_OTP_FILE ]; then
  echo "Please, remove the file $CRV_OTP_FILE"
else
	while true
	do
	vncpasswd -o -display $DISPLAY 2>&1 | sed 's/^.*: //' > $CRV_OTP_FILE
	sleep 50
	done 
fi