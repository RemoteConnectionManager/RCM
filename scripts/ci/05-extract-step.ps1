$ErrorActionPreference = 'Stop'

New-Item -ItemType Directory -Path "${env:RCM_CHECKOUT}\tmp" -Force

# Download step
Invoke-WebRequest -URI "${env:SMALLSTEP_DOWNLOAD}/v${env:SMALLSTEP_VERSION}/step_windows_${env:SMALLSTEP_VERSION}_amd64.zip" -OutFile "${env:RCM_CHECKOUT}/tmp/step.zip"

# Make external directories
if (Test-Path "${env:RCM_CHECKOUT}\${env:SMALLSTEP_EXTERNAL}") {
    Remove-Item -Path "${env:RCM_CHECKOUT}\${env:SMALLSTEP_EXTERNAL}" -Force -Recurse
}
New-Item -ItemType Directory -Path "${env:RCM_CHECKOUT}\${env:SMALLSTEP_EXTERNAL}" -Force

# Extract and copy executable
Expand-Archive -LiteralPath "${env:RCM_CHECKOUT}\tmp\step.zip" -DestinationPath "${env:RCM_CHECKOUT}\tmp"  -Force
Copy-Item "${env:RCM_CHECKOUT}\tmp\step*\bin\step.exe" -Destination "${env:RCM_CHECKOUT}\${env:SMALLSTEP_EXTERNAL}"
