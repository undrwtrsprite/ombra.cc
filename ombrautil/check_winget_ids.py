"""One-off script to verify all INSTALLER_CATEGORIES winget IDs. Run from ombrautil dir."""
import subprocess
import sys

INSTALLER_CATEGORIES = {
    "Browsers": [
        ("Google Chrome", "Google.Chrome"),
        ("Mozilla Firefox", "Mozilla.Firefox"),
        ("Microsoft Edge", "Microsoft.Edge"),
        ("Brave Browser", "Brave.Brave"),
        ("Opera", "Opera.Opera"),
    ],
    "Media & Documents": [
        ("VLC Media Player", "VideoLAN.VLC"),
        ("Adobe Acrobat Reader DC", "Adobe.Acrobat.Reader.64-bit"),
        ("LibreOffice", "TheDocumentFoundation.LibreOffice"),
        ("Sumatra PDF", "SumatraPDF.SumatraPDF"),
        ("HandBrake", "HandBrake.HandBrake"),
    ],
    "Development": [
        ("Visual Studio Code", "Microsoft.VisualStudioCode"),
        ("Python 3.12", "Python.Python.3.12"),
        ("Node.js LTS", "OpenJS.NodeJS.LTS"),
        ("Git", "Git.Git"),
        ("Docker Desktop", "Docker.DockerDesktop"),
        ("Windows Terminal", "Microsoft.WindowsTerminal"),
        ("PuTTY", "PuTTY.PuTTY"),
        ("WinSCP", "WinSCP.WinSCP"),
    ],
    "Communication": [
        ("Discord", "Discord.Discord"),
        ("Zoom", "Zoom.Zoom"),
        ("Slack", "SlackTechnologies.Slack"),
        ("Telegram", "Telegram.TelegramDesktop"),
        ("Microsoft Teams", "Microsoft.Teams"),
    ],
    "Utilities & Tools": [
        ("7-Zip", "7zip.7zip"),
        ("Notepad++", "Notepad++.Notepad++"),
        ("Microsoft PowerToys", "Microsoft.PowerToys"),
        ("Everything (search)", "voidtools.Everything"),
        ("ShareX", "ShareX.ShareX"),
        ("Greenshot", "Greenshot.Greenshot"),
        ("KeePass", "DominikReichl.KeePass"),
        ("WinRAR", "RARLab.WinRAR"),
        ("CCleaner", "Piriform.CCleaner"),
    ],
    "Gaming & Entertainment": [
        ("Steam", "Valve.Steam"),
        ("Spotify", "Spotify.Spotify"),
        ("OBS Studio", "OBSProject.OBSStudio"),
        ("qBittorrent", "qBittorrent.qBittorrent"),
    ],
    "Photo & Design": [
        ("GIMP", "GIMP.GIMP.2"),
        ("Paint.NET", "dotPDN.PaintDotNet"),
        ("IrfanView", "IrfanSkiljan.IrfanView"),
    ],
    "Remote & Security": [
        ("TeamViewer", "TeamViewer.TeamViewer"),
        ("AnyDesk", "AnyDesk.AnyDesk"),
        ("Malwarebytes", "Malwarebytes.Malwarebytes"),
    ],
    "Audio & Video": [
        ("Audacity", "Audacity.Audacity"),
    ],
}

def check_id(app_id):
    try:
        r = subprocess.run(
            ["winget", "show", "--id", app_id, "-e"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        return r.returncode == 0
    except Exception:
        return False

bad = []
for cat, apps in INSTALLER_CATEGORIES.items():
    for name, app_id in apps:
        if not check_id(app_id):
            bad.append((cat, name, app_id))
            print(f"FAIL: {cat} / {name} -> {app_id}")
        else:
            print(f"OK:   {name} ({app_id})")

if bad:
    print("\n--- Need to fix (search winget for correct ID): ---")
    for c, n, i in bad:
        print(f"  {n}: {i}")
    sys.exit(1)
print("\nAll IDs valid.")
sys.exit(0)
