Set-StrictMode -Version Latest

# https://www.7-zip.org/a/7zr.exe
choco install --no-progress 7zip
$URL = "${{ env.GIT_DOWNLOAD }}/v${{ env.GIT_VERSION }}.windows.1/PortableGit-${{ env.GIT_VERSION }}-64-bit.7z.exe"
Write-Output $URL
Invoke-WebRequest -URI $URL -OutFile git.7zip
7z.exe x -ogit git.7zip