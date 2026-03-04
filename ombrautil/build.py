"""
Build OmbraUtility.exe and force the icon onto the exe with rcedit
(PyInstaller often fails to embed the icon; rcedit applies it after build.)

Requirements:
  - PyInstaller, Pillow (pip install pyinstaller Pillow)
  - Node.js (for npx rcedit) — https://nodejs.org
     If you don't have Node, after building run manually:
     npx rcedit dist\\OmbraUtility.exe --set-icon icon.ico
"""
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

DIST_EXE = os.path.join(SCRIPT_DIR, "dist", "Ombra Utility Pro.exe")
ICON_ICO = os.path.join(SCRIPT_DIR, "icon.ico")

def run(cmd, description):
    print("\n--- %s ---" % description)
    print(" ".join(cmd) if isinstance(cmd, list) else cmd)
    r = subprocess.run(cmd, shell=(isinstance(cmd, str)))
    if r.returncode != 0:
        print("Failed:", description)
        sys.exit(r.returncode)

def main():
    # 1) Ensure icon.ico is valid (Pillow multi-size)
    try:
        from PIL import Image
        run([sys.executable, "create_icon.py"], "Create/fix icon.ico")
    except ImportError:
        if not os.path.isfile(ICON_ICO):
            print("Missing icon.ico. Add icon.ico or icon.png and run: pip install Pillow && python create_icon.py")
            sys.exit(1)
        print("Skipping create_icon (install Pillow to fix icon format). Using existing icon.ico")

    # 2) Clean and build
    for d in ("build", "dist"):
        p = os.path.join(SCRIPT_DIR, d)
        if os.path.isdir(p):
            import shutil
            shutil.rmtree(p, ignore_errors=True)
    run([sys.executable, "-m", "PyInstaller", "OmbraUtility.spec"], "PyInstaller build")

    if not os.path.isfile(DIST_EXE):
        print("Build failed: exe not found at", DIST_EXE)
        sys.exit(1)

    # 3) Apply icon with rcedit (bypasses PyInstaller icon issues)
    if not os.path.isfile(ICON_ICO):
        print("icon.ico not found; skipping rcedit.")
        return
    r = subprocess.run(
        ["npx", "--yes", "rcedit", DIST_EXE, "--set-icon", ICON_ICO],
        capture_output=True,
        text=True,
        cwd=SCRIPT_DIR,
    )
    if r.returncode == 0:
        print("\nIcon applied to exe with rcedit.")
    else:
        print("\n" + "=" * 60)
        print("rcedit failed (icon not set). Install Node.js from https://nodejs.org")
        print("Then run this in the ombrautil folder:")
        print('  npx rcedit "dist\\Ombra Utility Pro.exe" --set-icon icon.ico')
        print("=" * 60)
        if r.stderr:
            print(r.stderr)

if __name__ == "__main__":
    main()
