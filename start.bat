@echo off
cd /d "%~dp0"
echo Open http://127.0.0.1:8000 after the server starts.
echo Keep this window open while using CampusGuide.
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 app.py
  goto done
)
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
  "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" app.py
  goto done
)
python app.py
:done
pause
