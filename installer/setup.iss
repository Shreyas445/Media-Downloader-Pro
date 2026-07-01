; ============================================================
; Media Downloader Pro — Inno Setup 7 Installer Script
; Professional Windows installer with FFmpeg bundling
; ============================================================

#define MyAppName "Media Downloader Pro"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "AntiGravity"
#define MyAppURL "https://github.com/Shreyas445/Media-Downloader-Pro"
#define MyAppExeName "Media Downloader Pro.exe"

[Setup]
; Unique App ID — DO NOT change this once published
AppId={{A7B3C9D1-E2F4-4A5B-8C6D-7E8F9A0B1C2D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; No admin required — installs per-user
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist\installer
OutputBaseFilename=MediaDownloaderPro_v{#MyAppVersion}_Setup
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
; Modern visual style
WizardStyle=modern
WizardSizePercent=110

; Minimum Windows 10
MinVersion=10.0

; Signing (optional — uncomment if you have a code signing cert)
; SignTool=signtool sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 /a $f

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main application (PyInstaller --onedir output)
Source: "..\dist\Media Downloader Pro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; FFmpeg binaries — bundled alongside the app in a 'tools' subfolder
Source: "..\tools\ffmpeg\ffmpeg.exe"; DestDir: "{app}\tools"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\tools\ffmpeg\ffprobe.exe"; DestDir: "{app}\tools"; Flags: ignoreversion skipifsourcedoesntexist

; App icon for uninstaller display
Source: "..\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"

; Start Menu uninstall shortcut
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional, user chooses during install)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
; Launch app after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up any leftover files
Type: filesandordirs; Name: "{app}\tools"
Type: filesandordirs; Name: "{app}\__pycache__"
