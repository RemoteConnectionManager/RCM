$ErrorActionPreference = 'Stop'

# Find java.securty and patch it
$JAVA_SECURITY = Get-ChildItem -Path "${env:RCM_CHECKOUT}/${env:TURBOVNC_EXTERNAL}" -Filter java.security -Recurse | ForEach-Object {$_.FullName}
(Get-Content "${JAVA_SECURITY}").replace("${env:ORIG_LINE}", "${env:NEW_LINE}") | Set-Content "${JAVA_SECURITY}"
