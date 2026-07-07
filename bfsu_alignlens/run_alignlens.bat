@echo off
chcp 65001
cd /d "%~dp0"
python -m pip install -U pip
python -m pip install -r requirements.txt
python main.py
pause
