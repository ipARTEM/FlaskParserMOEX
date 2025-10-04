@echo off
call .\.venv\Scripts\activate
set FLASK_ADMIN_TOKEN=set-your-strong-admin-token
python run.py
