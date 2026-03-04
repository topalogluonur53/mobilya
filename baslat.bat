@echo off
echo ===========================================
echo Mutfak Dolabi Planlayici Baslatiliyor...
echo ===========================================

REM Sanal ortami aktiflestir
call venv\Scripts\activate.bat

REM Tarayiciyi otomatik olarak ac
start http://127.0.0.1:8000/

REM Django sunucusunu baslat
python manage.py runserver

pause
