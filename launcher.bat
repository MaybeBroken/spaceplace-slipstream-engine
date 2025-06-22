@echo off
echo launching from %cd%
echo Checking paths...
if not exist "requirements.txt" (
  echo Requirements file not found at "requirements.txt"
  pause
)
if not exist "runner.py" (
  echo Main script not found at "runner.py"
  pause
)
python3 --version >nul 2>&1
if %errorlevel% neq 0 (
  echo Python3 is not installed. Installing from Microsoft Store...
  start ms-windows-store://pdp/?productid=9PJPW5LDXLZ5
  echo Waiting for Python3 installation to complete...
  :wait_for_python
  timeout /t 1 >nul
  python3 --version >nul 2>&1
  if %errorlevel% neq 0 (
    goto wait_for_python
  )
)
echo Paths are correct.
python3 -m pip install -r "requirements.txt" > pip-output.dat
python3 "runner.py" > base-output.dat
echo PIP output has been saved to %cd%\pip-output.dat
echo Python output has been saved to %cd%\base-output.dat
echo Engine output has been saved to %cd%\engine-debug.dat
pause
