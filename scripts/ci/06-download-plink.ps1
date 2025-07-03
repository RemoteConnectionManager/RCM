$ErrorActionPreference = 'Stop'


# Make external directories
if (Test-Path "${env:RCM_CHECKOUT}\rcm\client\external\plink") {
    Remove-Item -Path "${env:RCM_CHECKOUT}\rcm\client\external\plink" -Force -Recurse
}
New-Item -ItemType Directory -Path "${env:RCM_CHECKOUT}\rcm\client\external\plink" -Force

# Download step
Invoke-WebRequest -URI "https://the.earth.li/~sgtatham/putty/latest/w64/plink.exe" -OutFile "${env:RCM_CHECKOUT}\rcm\client\external\plink\plink.exe"
