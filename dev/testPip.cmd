@echo OFF
cd ..
rmdir /s /q build
rmdir /s /q dist
python setup.py sdist bdist_wheel
pip uninstall nsz -y
pip install .
pause
