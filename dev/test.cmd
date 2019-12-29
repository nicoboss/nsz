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
python ..\nsz.py -V .
del *.nsz *.xcz
python ..\nsz.py -l 8 -V -S -C .
del *.nsz *.xcz
python ..\nsz.py -l 8 -V -B -C .
del *.nsp *.xci
nsz -D -V .
cd ..
goto :eof

:Test2
rmdir /s /q build
rmdir /s /q dist
python setup.py sdist bdist_wheel
pip uninstall nsz -y
pip install .
cd ROMs
nsz -V .
del *.nsz *.xcz
nsz -l 8 -V -S -C .
del *.nsz *.xcz
nsz -l 8 -V -B -C .
del *.nsp *.xci
nsz -D -V .
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
..\nsz\dist\__init__\nsz.exe -V .
del *.nsz *.xcz
..\nsz\dist\__init__\nsz.exe -l 8 -S -V -C .
del *.nsz *.xcz
..\nsz\dist\__init__\nsz.exe -l 8 -V -B -C .
del *.nsp *.xci
..\nsz\dist\__init__\nsz.exe -D -V .
cd ..
goto :eof
