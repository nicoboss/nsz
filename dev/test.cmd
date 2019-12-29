@echo OFF

REM Tests
cd ..
call :Test1
pause
call :Test2
pause
call :Test3
pause
goto :eof


:Test1
cd ROMs
del *.nsz
python ..\nsz.py -l 8 -V -C .
del *.nsz
python ..\nsz.py -l 8 -V -B -C .
cd ..
goto :eof

:Test2
python setup.py sdist bdist_wheel
pip uninstall nsz -y
pip install .
cd ROMs
del *.nsz
nsz -l 8 -V -C .
del *.nsz
nsz -l 8 -V -B -C .
cd ..
goto :eof

:Test3
cd nsz
rmdir /s /q build
rmdir /s /q dist
ping 127.0.0.1 -n 2 >NUL
pyinstaller .\__init__.spec
mkdir dist\__init__\gui
cd ..
cd ROMs
del *.nsz
..\nsz\dist\__init__\nsz.exe -l 8 -V -C .
del *.nsz
..\nsz\dist\__init__\nsz.exe -l 8 -V -B -C .
cd ..
goto :eof
