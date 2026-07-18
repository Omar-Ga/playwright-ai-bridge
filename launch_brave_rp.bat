@echo off
set PROFILE=Profile 1
if not "%~1"=="" set PROFILE=%~1

title Brave RP Profile (%PROFILE%) - Debug Mode
echo.
echo  ==========================================
echo   Launching Brave (Default/Profile Picker)
echo   Remote debugging on port 9222
echo  ==========================================
echo.

start "" "C:\Users\Omar\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe" ^
  --remote-debugging-port=9222 ^
  --no-first-run ^
  --no-default-browser-check

echo  [OK] Brave launched!
echo  [OK] CDP listening on http://127.0.0.1:9222
echo.
echo  You can now tell the AI to attach.
echo  Do NOT close this window until done.
echo.
pause
