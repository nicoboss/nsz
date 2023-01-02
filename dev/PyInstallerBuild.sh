pip3 install -r ./requirements-pyinstaller.txt
cd ../nsz
rm -rf build
rm -rf dist
pyinstaller ./__init__.spec
cd dist/__init__
read -p "Press any key to test ..."
./nsz.exe
