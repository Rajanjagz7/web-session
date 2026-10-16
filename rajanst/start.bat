@echo off
cd /d "%~dp0"
echo Rajan Algo - http://localhost:8000
start "" http://localhost:8000
python -m uvicorn server:app --host 127.0.0.1 --port 8000
