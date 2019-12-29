@echo OFF
cd ..\nsz
rmdir /s /q build
rmdir /s /q dist
ping 127.0.0.1 -n 2 >NUL
pyinstaller .\__init__.spec
cd dist\__init__
mkdir gui
pause
.\nsz.exe
pause
