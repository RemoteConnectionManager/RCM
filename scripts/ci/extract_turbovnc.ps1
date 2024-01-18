Set-StrictMode -Version Latest

# Download exe
Invoke-WebRequest -URI "${env:TURBOVNC_DOWNLOAD}/${env:TURBOVNC_VERSION}/TurboVNC-${env:TURBOVNC_VERSION}-x64.exe" -OutFile turbovnc.exe 

# Extract file from exe
choco install --no-progress innoextract
innoextract turbovnc.exe
mv app turbovnc