echo %~dp0
rem cd %~dp0\pyinstaller-1.5.1
python %~dp0\..\PyInstaller\pyinstaller-1.5.1\Build.py %~dp0\..\spec_files\crv_client_tk.spec
