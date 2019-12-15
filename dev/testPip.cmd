cd ..
python setup.py sdist bdist_wheel
pip uninstall nsz -y
pip install .
pause
