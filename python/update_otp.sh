#!/bin/bash
while true
do
vncpasswd -o -display $DISPLAY 2>&1 | sed 's/^.*: //' > $CRV_OTP_FILE
sleep 50
done 