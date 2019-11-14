@echo OFF
cd ..
del keys.txt
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q nsz\__pycache__
rmdir /s /q nsz\Fs\__pycache__
rmdir /s /q nsz\nut\__pycache__
rmdir /s /q nsz\nut\___init__.build
python setup.py sdist bdist_wheel
python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
ping 127.0.0.1 -n 31 >NUL
call :Test1
pause
python -m twine upload dist/*
ping 127.0.0.1 -n 31 >NUL
call :Test2
pause


:Test1
pip uninstall nsz -y
pip install --index-url https://test.pypi.org/simple/ --no-deps nsz
cd ROMs
del *.nsz
nsz -C -V . -l 0
del *.nsz
nsz -B -C -V .
del *.nsz
cd ..
goto :eof

:Test2
pip uninstall nsz -y
pip install nsz
cd ROMs
del *.nsz
nsz -C -V . -l 0
del *.nsz
nsz -B -C -V .
del *.nsz
cd ..
goto :eof
