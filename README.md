<div align="center">
    <img src="icon.png" width="128" height="128" alt="Media Downloader Pro Logo" />
    <h1>Media Downloader Pro</h1>
    <p>Download YouTube videos, MP3 audio, and Instagram reels — all from one beautiful desktop app.</p>
</div>

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.10%2B-brightgreen.svg)
![Framework](https://img.shields.io/badge/framework-PyWebView-orange.svg)
![Version](https://img.shields.io/badge/version-2.0.0-purple.svg)

## 🔮 Overview

**Media Downloader Pro** is a sleek Windows desktop application that wraps the powerful `yt-dlp` engine inside a gorgeous glassmorphism UI. Download YouTube videos in up to 4K, extract MP3 audio at any bitrate, and grab Instagram reels/posts — all without touching the terminal.

## ✨ Features

- **🎨 Glassmorphism Interface** — Sleek dark theme with platform-aware accents (purple for YouTube, gradient for Instagram)
- **📹 YouTube Downloads** — MP4 video (4K/1080p/720p/480p) and MP3 audio (128-320kbps)
- **📸 Instagram Downloads** — Public reels and posts with one-click download
- **📂 Custom Save Location** — Native Windows folder picker via PyWebView
- **🎵 Chapter Splitting** — Auto-split albums/podcasts into individual tracks
- **🔧 Bundled FFmpeg** — No external dependencies needed on the target machine
- **📦 Professional Installer** — Inno Setup 7 installer with Start Menu, Desktop shortcut, and uninstaller

## 🚀 Getting Started

### For Users (Just Want the App)

1. Download `MediaDownloaderPro_v2.0.0_Setup.exe` from the [Releases](https://github.com/Shreyas445/Media-Downloader-Pro/releases) page
2. Run the installer — no admin rights required
3. Find "Media Downloader Pro" in your Start Menu

### For Developers

#### Prerequisites
- **Python 3.10+**
- **Inno Setup 7** (for building the installer)

#### Local Development
```bash
git clone https://github.com/Shreyas445/Media-Downloader-Pro.git
cd Media-Downloader-Pro
pip install pywebview yt-dlp pillow
python main.py
```

#### Building the Installer
```cmd
build.bat
```
This automated script will:
1. Install all Python dependencies
2. Download FFmpeg binaries (if not already present)
3. Generate the app icon from `icon.png`
4. Compile the app with PyInstaller (onedir mode)
5. Package everything into a professional Windows installer using Inno Setup 7

The final installer will be at: `dist/installer/MediaDownloaderPro_v2.0.0_Setup.exe`

## 📁 Project Structure

```
Media Downloader Pro/
├── main.py                 # Backend — YouTube + Instagram download logic
├── ui/
│   ├── index.html          # Multi-platform UI layout
│   ├── app.js              # Frontend logic with platform detection
│   └── style.css           # Glassmorphism theme with platform-aware colors
├── installer/
│   └── setup.iss           # Inno Setup 7 installer script
├── tools/
│   └── ffmpeg/             # Bundled FFmpeg binaries (auto-downloaded)
├── build.bat               # Full build pipeline
├── icon.png                # Source app icon
└── README.md
```

## 🛡️ How It Works

The app uses `yt-dlp` (a powerful media extraction library) as its backend engine, with `FFmpeg` for audio conversion and video muxing. The UI is built with PyWebView, which renders a native web-based interface without requiring a browser.

**Key design decision**: FFmpeg is bundled alongside the app so end users don't need to install anything separately. The build script automatically downloads FFmpeg and the Inno Setup installer packages everything into a single setup executable.

---
*Built with ❤ by AntiGravity*
