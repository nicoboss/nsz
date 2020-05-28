@echo off
python nsz.py -D .\dummy.nsz
if errorlevel 1 (
   echo Failure Reason Given is %errorlevel%
)
pause
