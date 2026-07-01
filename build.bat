@echo off
setlocal enabledelayedexpansion

echo.
echo  =====================================================
echo   Media Downloader Pro v2.0 — Full Build Pipeline
echo  =====================================================
echo.

set "PROJECT_DIR=%~dp0"
set "TOOLS_DIR=%PROJECT_DIR%tools\ffmpeg"
set "DIST_DIR=%PROJECT_DIR%dist"
set "INNO_COMPILER=C:\Program Files\Inno Setup 7\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 7\ISCC.exe" set "INNO_COMPILER=C:\Program Files (x86)\Inno Setup 7\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "INNO_COMPILER=C:\Program Files\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "INNO_COMPILER=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 7\ISCC.exe" set "INNO_COMPILER=C:\Program Files\Inno Setup 7\ISCC.exe"

:: =====================================================
:: STEP 1: Install Python dependencies
:: =====================================================
echo [1/5] Installing Python dependencies...
pip install pyinstaller pywebview yt-dlp pillow instaloader > build_log.txt 2>&1
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies. Check build_log.txt
    goto :error
)
echo       Done.
echo.

:: =====================================================
:: STEP 2: Download FFmpeg (if not already present)
:: =====================================================
echo [2/5] Checking for FFmpeg...
if not exist "%TOOLS_DIR%\ffmpeg.exe" (
    echo       FFmpeg not found in tools folder. Looking locally...
    
    if not exist "%TOOLS_DIR%" mkdir "%TOOLS_DIR%"
    
    :: Try copying from system PATH first
    where ffmpeg >nul 2>nul
    if not errorlevel 1 (
        echo       Found FFmpeg in system PATH. Copying...
        for /f "delims=" %%I in ('where ffmpeg') do (
            if not exist "%TOOLS_DIR%\ffmpeg.exe" copy "%%I" "%TOOLS_DIR%\ffmpeg.exe" >nul
        )
        for /f "delims=" %%I in ('where ffprobe') do (
            if not exist "%TOOLS_DIR%\ffprobe.exe" copy "%%I" "%TOOLS_DIR%\ffprobe.exe" >nul
        )
    )

    :: Try copying from user's local FFmpeg install first
    if not exist "%TOOLS_DIR%\ffmpeg.exe" (
        set "LOCAL_FFMPEG=C:\Users\SHREYAS\Downloads\ffmpeg\ffmpeg-2025-11-27-git-61b034a47c-full_build\bin"
        if exist "!LOCAL_FFMPEG!\ffmpeg.exe" (
            echo       Found local FFmpeg. Copying...
            copy "!LOCAL_FFMPEG!\ffmpeg.exe" "%TOOLS_DIR%\ffmpeg.exe" >nul
            copy "!LOCAL_FFMPEG!\ffprobe.exe" "%TOOLS_DIR%\ffprobe.exe" >nul
            echo       Copied from local install.
        )
    )
    
    if not exist "%TOOLS_DIR%\ffmpeg.exe" (
        echo       No local FFmpeg found. Downloading from gyan.dev...
        set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        set "FFMPEG_ZIP=%PROJECT_DIR%tools\ffmpeg_download.zip"
        
        curl -L -o "!FFMPEG_ZIP!" "!FFMPEG_URL!" >> build_log.txt 2>&1
        if errorlevel 1 (
            echo ERROR: Failed to download FFmpeg. 
            echo        Please manually place ffmpeg.exe and ffprobe.exe in: %TOOLS_DIR%\
            goto :error
        )
        
        echo       Extracting ffmpeg.exe and ffprobe.exe...
        powershell -NoProfile -Command "& { $zip = '%TOOLS_DIR%\..\ffmpeg_download.zip'; $extractPath = '%TOOLS_DIR%\..\_ffmpeg_temp'; Expand-Archive -Path $zip -DestinationPath $extractPath -Force; $binDir = Get-ChildItem -Path $extractPath -Recurse -Directory -Filter 'bin' | Select-Object -First 1; if ($binDir) { Copy-Item (Join-Path $binDir.FullName 'ffmpeg.exe') '%TOOLS_DIR%\ffmpeg.exe' -Force; Copy-Item (Join-Path $binDir.FullName 'ffprobe.exe') '%TOOLS_DIR%\ffprobe.exe' -Force }; Remove-Item $extractPath -Recurse -Force; Remove-Item $zip -Force }" >> build_log.txt 2>&1
    )
    
    if not exist "%TOOLS_DIR%\ffmpeg.exe" (
        echo ERROR: Failed to get FFmpeg.
        echo        Please manually place ffmpeg.exe and ffprobe.exe in:
        echo        %TOOLS_DIR%\
        goto :error
    )
    echo       FFmpeg downloaded and extracted successfully.
) else (
    echo       FFmpeg found at %TOOLS_DIR%
)
echo.

:: =====================================================
:: STEP 3: Generate icon
:: =====================================================
echo [3/5] Generating application icon...
python icon_converter.py >> build_log.txt 2>&1
echo       Done.
echo.

:: =====================================================
:: STEP 4: Build with PyInstaller (onedir mode)
:: =====================================================
echo [4/5] Building application with PyInstaller (this may take a few minutes)...

:: Clean previous build
if exist "%DIST_DIR%\Media Downloader Pro" rmdir /s /q "%DIST_DIR%\Media Downloader Pro"

pyinstaller -y --noconsole --name "Media Downloader Pro" ^
    --add-data "ui;ui" ^
    --add-data "tools\ffmpeg\ffmpeg.exe;tools" ^
    --add-data "tools\ffmpeg\ffprobe.exe;tools" ^
    --icon=icon.ico ^
    --distpath "%DIST_DIR%" ^
    main.py >> build_log.txt 2>&1

if errorlevel 1 (
    echo ERROR: PyInstaller build failed. Check build_log.txt
    goto :error
)
echo       Done. App built to: %DIST_DIR%\Media Downloader Pro\
echo.

:: =====================================================
:: STEP 5: Build Inno Setup installer
:: =====================================================
echo [5/5] Building installer with Inno Setup 7...

:: Create installer output directory
if not exist "%DIST_DIR%\installer" mkdir "%DIST_DIR%\installer"

"%INNO_COMPILER%" "%PROJECT_DIR%installer\setup.iss" >> build_log.txt 2>&1
if errorlevel 1 (
    echo ERROR: Inno Setup compilation failed. Check build_log.txt
    goto :error
)

echo       Done.
echo.
echo  =====================================================
echo   BUILD COMPLETE!
echo  =====================================================
echo.
echo   [SUCCESS] Setup file built successfully using Inno Setup!
echo   Installer available at: %DIST_DIR%\installer\MediaDownloaderPro_v2.0.0_Setup.exe
echo   App folder available at: %DIST_DIR%\Media Downloader Pro\
echo.
echo   You can now share MediaDownloaderPro_v2.0.0_Setup.exe with anyone!
echo  =====================================================
goto :done

:error
echo.
echo  BUILD FAILED — check build_log.txt for details.
echo.

:done
echo.
