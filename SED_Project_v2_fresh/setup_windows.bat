
@echo off
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python build_exe.py
echo Build complete. See dist\SED_App_v2.exe
pause
