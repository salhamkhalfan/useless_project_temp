@echo off
echo Starting TOUCH GRASS server at http://127.0.0.1:8000
call "C:\UP3.0\useless-env\Scripts\activate.bat"
python -m uvicorn app:app --host 127.0.0.1 --port 8000