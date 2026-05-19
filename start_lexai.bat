@echo off

cd /d C:\LexAI

echo Activating virtual environment...
call C:\LexAI\venv\Scripts\activate.bat

echo Checking Python path...
where python

echo Starting LexAI...

start http://localhost:5000

python app.py

pause