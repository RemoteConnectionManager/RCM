Set-StrictMode -Version Latest

$URL = "${env:SMALLSTEP_DOWNLOAD}/v${env:SMALLSTEP_VERSION}/step_windows_${env:SMALLSTEP_VERSION}_amd64.zip"
Write-Output $URL
Invoke-WebRequest -URI $URL -OutFile step.zip
Expand-Archive -LiteralPath .\step.zip -DestinationPath .
mv step* step