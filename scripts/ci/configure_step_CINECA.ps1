Set-StrictMode -Version Latest

step\bin\step.exe ca bootstrap --ca-url="https://sshproxy.hpc.cineca.it" --fingerprint "${env:CINECA_STEP_FINGERPRINT}"

#############################################
# TO BE REMOVED IF ARTIFACT ARE NOT REQUIRED
#############################################
Copy-Item -Path ${env:USERPROFILE}\.step -Destination .\.step -Recurse -Force
#############################################
