@echo off
echo ============================================
echo   Trading 212 AI Market Intelligence v2.0
echo ============================================
echo.
echo Installing packages...
pip install -r requirements.txt -q
echo.
echo Starting app at http://localhost:5000
echo.
python app.py
pause
