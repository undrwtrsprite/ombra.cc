"""
Build a proper Windows .ico with multiple sizes so the exe and window icon look correct everywhere:
- Window title bar (16x16), taskbar / Alt+Tab (32x32), Explorer / large (48+, 256).
Run once before: pyinstaller OmbraUtility.spec

  pip install Pillow
  python create_icon.py
"""
import os
import sys

try:
    from PIL import Image
except ImportError:
    print("Install Pillow first: pip install Pillow")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PNG = os.path.join(SCRIPT_DIR, "icon.png")
ICON_ICO = os.path.join(SCRIPT_DIR, "icon.ico")

# All sizes Windows uses: title bar, taskbar, alt-tab, explorer, high-DPI
SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

def main():
    if os.path.isfile(ICON_PNG):
        img = Image.open(ICON_PNG).convert("RGBA")
        print("Using icon.png")
    elif os.path.isfile(ICON_ICO):
        img = Image.open(ICON_ICO).convert("RGBA")
        print("Re-saving icon.ico with proper multi-size format (fixes window/taskbar scaling)")
    else:
        print("Put icon.png or icon.ico in this folder and run again.")
        sys.exit(1)

    # Use at least 256x256 as base so all smaller sizes are sharp
    if img.width < 256 or img.height < 256:
        img = img.resize((256, 256), Image.Resampling.LANCZOS)
    img.save(ICON_ICO, format="ICO", sizes=SIZES)
    print("Written:", ICON_ICO, "with sizes:", [f"{w}x{h}" for w, h in SIZES])

if __name__ == "__main__":
    main()
