$ErrorActionPreference = 'Stop'

New-Item -ItemType Directory -Path "${env:RCM_CHECKOUT}\tmp" -Force

# # Install innoextract locally
# Invoke-WebRequest -URI "https://github.com/dscharrer/innoextract/releases/download/1.9/innoextract-1.9-windows.zip" -OutFile "${env:RCM_CHECKOUT}\tmp\innoextract.zip"
# Expand-Archive -LiteralPath "${env:RCM_CHECKOUT}\tmp\innoextract.zip" -DestinationPath "${env:RCM_CHECKOUT}\tmp\innoextract" -Force

# Download turbovnc
$suffix = if ([version]${env:TURBOVNC_VERSION} -gt [version]"3.1.4") { "" } else { "-x64" }
Invoke-WebRequest -URI "${env:TURBOVNC_DOWNLOAD}/${env:TURBOVNC_VERSION}/TurboVNC-${env:TURBOVNC_VERSION}${suffix}.exe" -OutFile "${env:RCM_CHECKOUT}\tmp\turbovnc.exe"

# Extract from exe
& "${env:RCM_CHECKOUT}\tmp\turbovnc.exe" /SILENT /DIR="${env:RCM_CHECKOUT}\tmp\app"
Wait-Process (Get-Process turbovnc).id
Remove-Item "${env:RCM_CHECKOUT}\tmp\app\unins000*"
# Push-Location "${env:RCM_CHECKOUT}\tmp"
# .\innoextract\innoextract turbovnc.exe
# Pop-Location

# Copy extracted file to `"${env:RCM_CHECKOUT}\${env:TURBOVNC_EXTERNAL}"`
if (Test-Path "${env:RCM_CHECKOUT}\${env:TURBOVNC_EXTERNAL}") {
    Remove-Item -Path "${env:RCM_CHECKOUT}\${env:TURBOVNC_EXTERNAL}" -Force -Recurse
}
New-Item -ItemType Directory -Force -Path "${env:RCM_CHECKOUT}\${env:TURBOVNC_EXTERNAL}"
Move-Item -Path "${env:RCM_CHECKOUT}\tmp\app" -Destination "${env:RCM_CHECKOUT}\${env:TURBOVNC_EXTERNAL}\bin"
