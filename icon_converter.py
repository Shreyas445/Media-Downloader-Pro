import glob
from PIL import Image
import os
import sys

print("Locating icon.png in the project directory...")
icon_png_path = os.path.join(os.path.dirname(__file__), "icon.png")

if not os.path.exists(icon_png_path):
    print("Error: icon.png not found in the current directory!")
    sys.exit(1)

save_path = os.path.join(os.path.dirname(__file__), "icon.ico")

print(f"Reading icon from: {icon_png_path}")
img = Image.open(icon_png_path)

# Convert to RGBA to preserve transparency if it's not already
if img.mode != 'RGBA':
    img = img.convert('RGBA')

# Resize to ensure maximum compatibility for Windows Icons (perfectly square is best)
# PyInstaller respects 256x256 as the standard max layer for ICO files.
img = img.resize((256, 256), Image.Resampling.LANCZOS)

# Save as ICO with multiple embedded sizes for the optimal Windows experience
img.save(save_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])

print(f"Successfully created: {save_path}")
