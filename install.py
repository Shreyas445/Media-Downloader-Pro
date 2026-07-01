import os
import sys
import shutil
import winreg
import subprocess

APP_NAME = "Media Downloader Pro"
PUBLISHER = "AntiGravity"
VERSION = "1.0.0"

# Directories
LOCAL_APP_DATA = os.environ.get('LOCALAPPDATA')
START_MENU_DIR = os.path.join(os.environ.get('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs')

DEST_DIR = os.path.join(LOCAL_APP_DATA, 'Programs', APP_NAME)
START_MENU_LNK = os.path.join(START_MENU_DIR, f"{APP_NAME}.lnk")

SOURCE_EXE = os.path.join(os.path.dirname(__file__), 'dist', f'{APP_NAME}.exe')
SOURCE_ICO = os.path.join(os.path.dirname(__file__), 'icon.ico')

DEST_EXE = os.path.join(DEST_DIR, f'{APP_NAME}.exe')
DEST_ICO = os.path.join(DEST_DIR, 'icon.ico')

# Uninstaller CMD string
UNINSTALL_CMD = (
    f'cmd.exe /c '
    f'rmdir /s /q "{DEST_DIR}" & '
    f'del /q "{START_MENU_LNK}" & '
    f'reg delete HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME.replace(" ", "")} /f'
)

def install():
    print(f"--- {APP_NAME} Installer ---")
    
    if not os.path.exists(SOURCE_EXE):
        print(f"Error: Could not find {SOURCE_EXE}")
        print("Please run build.bat to compile the .exe first!")
        sys.exit(1)

    print(f"1. Copying files to {DEST_DIR}...")
    os.makedirs(DEST_DIR, exist_ok=True)
    shutil.copy2(SOURCE_EXE, DEST_EXE)
    if os.path.exists(SOURCE_ICO):
        shutil.copy2(SOURCE_ICO, DEST_ICO)

    print(f"2. Creating Start Menu Shortcut...")
    vbs_script_path = os.path.join(DEST_DIR, "createshortcut.vbs")
    vbs_content = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{START_MENU_LNK}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{DEST_EXE}"
oLink.IconLocation = "{DEST_ICO}"
oLink.WorkingDirectory = "{DEST_DIR}"
oLink.Save
"""
    with open(vbs_script_path, 'w') as f:
        f.write(vbs_content)
    
    # Run the VBScript to create the link, then delete the temp script
    subprocess.run(['cscript.exe', '//Nologo', vbs_script_path], shell=True)
    os.remove(vbs_script_path)

    print(f"3. Registering App with Windows Settings...")
    registry_path = f"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME.replace(' ', '')}"
    
    try:
        # Create key in HKEY_CURRENT_USER (No admin rights needed, entirely safe)
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, registry_path)
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, VERSION)
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, DEST_ICO)
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, UNINSTALL_CMD)
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Warning: Could not add to registry: {e}")

    print("\n=============================================")
    print(f"SUCCESS! {APP_NAME} is now fully installed.")
    print("You can now find your application by hitting the Windows Key and typing its name, or view it in 'Add/Remove Programs'!")
    print("=============================================\n")

if __name__ == "__main__":
    install()
