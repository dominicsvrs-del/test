@echo off
cd /d "%~dp0"
set /p URL=Twitch-Link (Kanal oder VOD) einfuegen: 
set /p HK=Hochkant fuer TikTok/Shorts? (j/n): 
if /i "%HK%"=="j" (python twitch_clipper.py "%URL%" --hochkant) else (python twitch_clipper.py "%URL%")
pause
