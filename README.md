<div align="center">
    <img src="icon.png" width="128" height="128" alt="Media Downloader Pro Logo" />
    <h1>Media Downloader Pro</h1>
    <p>A native, high-performance web-scraper and media extraction tool wrapped in a stunning PyWebView Glassmorphism UI.</p>
</div>

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.10%2B-brightgreen.svg)
![Framework](https://img.shields.io/badge/framework-PyWebView-orange.svg)

## 🔮 Overview

**Media Downloader Pro** solves the problem of unreliable command-line downloaders by wrapping the immensely powerful `yt-dlp` engine inside a beautiful, intuitive desktop application. Through a custom-built API linking Python and JavaScript, users can instantly analyze YouTube layouts and fetch localized formats—without wrestling with the terminal.

## ✨ Features

- **Gorgeous Glassmorphism Interface**: A sleek, dark-themed Windows 11 style UI crafted with modern CSS.
- **Dynamic Format Analyzer**: Fetches all available MP4 resolutions (4K, 1080p, 720p) and MP3 bitrates (320kbps, 192kbps, 128kbps) instantly.
- **Native OS Integration**: Features a native Microsoft Windows folder explorer for setting download paths via PyWebView.
- **Chapter Splitting**: Built-in support to auto-split massive albums or podcasts into designated MP3/MP4 tracks using FFmpeg metadata.
- **Single Executable Deployment**: Ships with an automated `build.bat` script that parses local assets into a distributable, standalone `.exe`.

## 🚀 Getting Started

### Prerequisites
Make sure you have **Python 3.10+** installed along with **FFmpeg** configured on your system PATH for audio generation. 

### Local Development Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/Shreyas445/Media-Downloader-Pro.git
   cd Media-Downloader-Pro
   ```

2. Install dependencies:
   ```bash
   pip install pywebview yt-dlp pillow pyinstaller==5.13.2
   ```

3. Run locally:
   ```bash
   python main.py
   ```

### 📦 Compiling to `.exe`

Media Downloader Pro includes a fully automated build script. Simply run:
```cmd
build.bat
```
This bat file will:
1. Dynamically read testing formats and package dependencies.
2. Render `icon.png` into a native `.ico` embedded logo.
3. Use PyInstaller (`--noconsole` and `--onefile`) to compress everything into a single transportable executable inside the `/dist/` folder!

---
*Created and optimized for high-quality UI/UX Desktop experiences.*
