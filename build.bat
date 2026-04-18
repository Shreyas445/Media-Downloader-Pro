@echo off
echo ===================================
echo   Building YouTube Downloader .exe
echo ===================================
echo.
echo Installing PyInstaller and Pillow...
pip install pyinstaller==5.13.2 pywebview yt-dlp pillow > build_log.txt 2>&1

echo.
echo Generating Application Icon...
python icon_converter.py >> build_log.txt 2>&1

echo.
echo Compiling the executable (This will take a few minutes)...
pyinstaller -y --noconsole --onefile --name "Media Downloader Pro" --add-data "ui;ui" --icon=icon.ico main.py >> build_log.txt 2>&1

echo.
echo ===================================
echo Done! 
echo Your .exe should be in the "dist" folder.
echo If it is still missing, please show me the build_log.txt file.
echo ===================================
pause
