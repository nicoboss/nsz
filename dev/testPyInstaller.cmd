cd ..\nsz
pyinstaller .\__init__.spec
cd dist\__init__
mkdir gui
pause
.\nsz.exe
pause
