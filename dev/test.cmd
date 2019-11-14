@echo OFF

REM Tests
cd ..
call :Test1
call :Test2
call :Test3
pause
goto :eof


:Test1
cd ROMs
del *.nsz
python ..\nsz.py -C -V . -l 0
del *.nsz
python ..\nsz.py -B -C -V .
del *.nsz
cd ..
goto :eof

:Test2
python setup.py sdist bdist_wheel
pip uninstall nsz -y
pip install .
cd ROMs
del *.nsz
nsz -C -V . -l 0
del *.nsz
nsz -B -C -V .
del *.nsz
cd ..
goto :eof

:Test3
cd nsz
rmdir /s /q __init__.dist
call nuitka __init__.py --standalone --plugin-enable=multiprocessing
move __init__.dist\__init__.exe __init__.dist\nsz.exe
rename __init__.dist nsz_win64_portable
rmdir /s /q ..\nsz_win64_portable
move nsz_win64_portable ..
cd ..
cd ROMs
del *.nsz
..\nsz_win64_portable\nsz.exe -C -V . -l 0
del *.nsz
..\nsz_win64_portable\nsz.exe -B -C -V .
del *.nsz
cd ..
goto :eof
