import os
import shutil
from collections import deque
import concurrent.futures
import threading
import time
import sys
import json
import platform
import subprocess
import webbrowser
import psutil
import pyperclip
import customtkinter as ctk
import socket
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog
from tkinter import ttk
from datetime import datetime
import winreg
import ctypes
from ctypes import wintypes
import math
import re
import hashlib
import urllib.request
import zipfile
import io
# Matplotlib imported lazily in setup_graph_widgets to speed startup

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- OMBRA.CC DARK INDIGO THEME ---
COLORS = {
    "bg":           "#09090b",
    "card":         "#18181b",
    "border":       "#27272a",
    "text":         "#fafafa",
    "subtext":      "#a1a1aa",
    "accent":       "#6366f1",
    "accent_hover": "#4f46e5",
    "success":      "#22c55e",
    "warning":      "#f59e0b",
    "danger":       "#ef4444",
    "hover":        "#27272a",
    "glass_edge":   "#3f3f46",
}

NAV_ICONS = {
    "Home": "🏠", "Install": "📦", "Tools": "🛠",
    "Scan": "📊", "System": "💻", "Settings": "⚙", "Logs": "📋",
}

# --- SOFTWARE INSTALLER CONFIG (category -> list of (display_name, winget_id)) ---
# All IDs are from the official winget repository (winget search <name> to verify).
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
# Flat dict for backward compatibility (name -> id)
SOFTWARE_TO_INSTALL = {name: app_id for _cat, apps in INSTALLER_CATEGORIES.items() for name, app_id in apps}

# --- CONSTANTS ---
DESKTOP_PATH = Path.home() / "Desktop"
DOWNLOADS_PATH = Path.home() / "Downloads"
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"

# Notification Constants
NOTIFICATION_WIDTH = 280
NOTIFICATION_SPACING = 6
NOTIFICATION_MARGIN_Y = 14
NOTIFICATION_MAX_VISIBLE = 3
NOTIFICATION_ACCENT_COLORS = {
    "info":    "#6366f1",
    "success": "#22c55e",
    "error":   "#ef4444",
    "warning": "#f59e0b",
}
NOTIFICATION_ICONS = {
    "info":    "\u2139",
    "success": "\u2713",
    "error":   "\u2717",
    "warning": "\u26A0",
}
CONFIG_FILE = Path("config.json")

# Fonts to preload so first use doesn't stall (family, size, bold)
_PRELOAD_FONTS = [
    ("Segoe UI", 11), ("Segoe UI", 11, "bold"), ("Segoe UI", 12), ("Segoe UI", 13), ("Segoe UI", 13, "bold"),
    ("Segoe UI", 14), ("Segoe UI", 14, "bold"), ("Segoe UI", 15), ("Segoe UI", 15, "bold"),
    ("Segoe UI Variable Display", 14, "bold"), ("Segoe UI Variable Display", 24, "bold"),
    ("Segoe UI Variable Display", 26, "bold"), ("Segoe UI Variable Display", 30, "bold"),
    ("Cascadia Code", 11), ("Consolas", 12),
]
# Tab names to preload in background after startup (order by likelihood of use)
_PRELOAD_TABS = ["Tools", "Scan", "Install", "System", "Settings", "Logs"]
DEFAULT_RULES = {
    "Visuals": [".jpg", ".png", ".webp", ".jpeg", ".gif", ".svg", ".heic"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv"],
    "Audio": [".mp3", ".wav", ".flac", ".aac"],
    "Docs": [".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".md"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Dev": [".py", ".ps1", ".js", ".html", ".css", ".json", ".xml", ".ipynb"],
    "Installers": [".exe", ".msi"],
}

# Windows API constants for desktop refresh
SHCNE_ASSOCCHANGED = 0x08000000
SHCNF_IDLIST = 0x0000

# Structure for sending files to recycle bin
class SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [
        ('hwnd', wintypes.HWND),
        ('wFunc', wintypes.UINT),
        ('pFrom', wintypes.LPCWSTR),
        ('pTo', wintypes.LPCWSTR),
        ('fFlags', wintypes.USHORT),
        ('fAnyOperationsAborted', wintypes.BOOL),
        ('hNameMappings', ctypes.c_void_p),
        ('lpszProgressTitle', wintypes.LPCWSTR)
    ]

# --- ADMIN HELPERS ---
def is_admin():
    """Checks if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin(restore_page=None):
    """Re-launches the script with administrative privileges and kills this process."""
    try:
        args = list(sys.argv)
        if restore_page:
            args = [a for a in args if not a.startswith("--restore-page=")]
            args.append(f"--restore-page={restore_page}")
        if getattr(sys, 'frozen', False):
            param = " ".join(args[1:]) if len(args) > 1 else None
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, param, None, 1)
        else:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(args), None, 1)
    except Exception as e:
        print(f"Failed to elevate privileges: {e}")
        return
    os._exit(0)

def send_to_recycle_bin(path_str: str) -> bool:
    """Moves a file to the recycle bin. Returns True on success."""
    # The path needs to be double-null-terminated for SHFileOperationW
    pFrom = path_str + '\0'
    
    file_op = SHFILEOPSTRUCTW()
    file_op.hwnd = None
    file_op.wFunc = 3  # FO_DELETE
    file_op.pFrom = pFrom
    file_op.pTo = None
    file_op.fFlags = 0x40 | 0x10  # FOF_ALLOWUNDO | FOF_NOCONFIRMATION
    
    result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(file_op))
    # Check if the operation was successful and not aborted by the user (if confirmation was on)
    return result == 0 and not file_op.fAnyOperationsAborted

def raise_process_priority():
    """Ask the OS to give this process more CPU time (Windows: Above Normal priority). Makes the app feel snappier when the system is busy."""
    if platform.system() != "Windows":
        return
    try:
        kernel32 = ctypes.windll.kernel32
        # ABOVE_NORMAL_PRIORITY_CLASS = 0x8000 — slightly more CPU than normal, not aggressive
        if kernel32.SetPriorityClass(kernel32.GetCurrentProcess(), 0x8000):
            pass  # Success
    except Exception:
        pass


def is_winget_available():
    """Checks if the winget command is available on the system."""
    try:
        subprocess.run(["winget", "--version"], capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def is_app_installed(app_id):
    """Returns True if the given winget package ID is installed. Used for single-app check and polling."""
    if not is_winget_available():
        return False
    try:
        r = subprocess.run(
            ["winget", "list", "--id", app_id, "-e"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if r.returncode != 0:
            return False
        return app_id in (r.stdout or "")
    except (FileNotFoundError, Exception):
        return False


def check_installed_software():
    """Uses winget to get a list of installed software and returns a set of package IDs (Id column)."""
    installed_ids = set()
    if not is_winget_available():
        return installed_ids
    try:
        result = subprocess.run(
            ["winget", "list", "--source", "winget"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        # Table columns: Name, Id, Version (and optionally Available, Source). Split by 2+ spaces to get columns.
        for line in result.stdout.splitlines():
            if not line.strip() or line.startswith("---"):
                continue
            if line.strip().startswith("Name") and "Id" in line:
                continue
            parts = re.split(r"\s{2,}", line.strip())
            if len(parts) >= 2:
                # Id is the second column (index 1)
                pkg_id = parts[1].strip()
                if pkg_id and "." in pkg_id:
                    installed_ids.add(pkg_id)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return installed_ids


# --- Installer: live search ---
INSTALLER_SEARCH_DEBOUNCE_MS = 450
INSTALLER_SEARCH_TIMEOUT = 15
INSTALLER_SEARCH_LIMIT = 25
INSTALLER_INSTALL_TIMEOUT = 600  # 10 min max for one install
INSTALLER_ACTION_BUTTON_WIDTH = 100  # Fixed width so Install and Uninstall buttons align
INSTALLER_ACTION_AREA_WIDTH = 240  # Fixed width for right-side area so Install and Uninstall rows align


def search_winget(query, limit=INSTALLER_SEARCH_LIMIT, timeout_sec=INSTALLER_SEARCH_TIMEOUT):
    """Search winget for packages. Returns list of dicts: {name, id, version, source='winget'}. Empty on error or timeout."""
    if not query or not is_winget_available():
        return []
    try:
        proc = subprocess.run(
            ["winget", "search", query, "--accept-source-agreements", "--disable-interactivity"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if proc.returncode != 0:
            return []
        out = (proc.stdout or "").strip()
        results = []
        lines = out.splitlines()
        # Find header line (Name, Id, Version, ...)
        header_idx = None
        for i, line in enumerate(lines):
            if "Id" in line and ("Name" in line or "Name " in line):
                header_idx = i
                break
        if header_idx is None:
            return []
        data_start = header_idx + 1
        for line in lines[data_start:]:
            if len(results) >= limit:
                break
            line = line.rstrip()
            if not line or line.startswith("---"):
                continue
            # Winget table: columns are often separated by 2+ spaces; Id is usually last significant token before Version/Available
            parts = re.split(r"\s{2,}", line.strip())
            if len(parts) >= 2:
                name = parts[0].strip()
                pkg_id = parts[1].strip()
                version = parts[2].strip() if len(parts) > 2 else ""
                if name and pkg_id and "." in pkg_id:
                    results.append({"name": name, "id": pkg_id, "version": version, "source": "winget"})
        return results
    except subprocess.TimeoutExpired:
        return []
    except (FileNotFoundError, Exception):
        return []




# Microsoft Store link for App Installer (enables winget on older Windows)
WINGET_APP_INSTALLER_STORE_URL = "https://apps.microsoft.com/store/detail/app-installer/9NBLGGH4NNS1"


def uninstall_winget(app_id, timeout_sec=120):
    """Run winget uninstall. Returns (success: bool, error_message: str or None)."""
    if not is_winget_available():
        return False, "Winget not available"
    try:
        r = subprocess.run(
            ["winget", "uninstall", "--id", app_id, "-e", "--silent"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if r.returncode == 0:
            return True, None
        # Winget sometimes returns non-zero (e.g. -1) even when uninstall succeeded; verify app is gone
        if not is_app_installed(app_id):
            return True, None
        err = (r.stderr or r.stdout or "").strip() or "Unknown error"
        return False, err
    except subprocess.TimeoutExpired:
        return False, "Uninstall timed out"
    except Exception as e:
        return False, str(e)


class GlobalHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app
    def on_modified(self, event):
        if self.app.realtime_active and not event.is_directory:
            self.app.after(0, self.app.debounce_sort)

class OmbraApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        raise_process_priority()
        self.withdraw()  # Keep hidden until fully built (splash is shown instead)

        self.realtime_active = False
        self.observer = None
        self.icons_hidden = False
        self.is_admin = is_admin()
        self._current_page = "Home"
        self.rules = dict(DEFAULT_RULES)
        self.installed_software_ids = set()
        self._installer_preload_done = False
        self._installer_preload_thread = None
        self._installer_search_timer = None
        self._installer_search_query_id = 0
        self._installer_search_results_container = None
        self.sort_timer = None
        self.ping_thread = None
        self._resize_after_id = None  # Debounce window resize
        self._system_info_cache = None  # Filled on first use (thread-safe: read after write on main)

        self.notification_counter = 0 # To give unique names to toasts for tracking
        # --- UI STATE ---
        self.active_toasts = []

        # --- GRAPH DATA ---
        self.data_points = 60 # Number of points to display on the graph (e.g., 60 points at 2s interval = 2 mins)
        self.cpu_data = deque([0] * self.data_points, maxlen=self.data_points)
        self.ram_data = deque([0] * self.data_points, maxlen=self.data_points)

        # --- UI STYLES ---
        self.button_styles = {
            "primary": {"fg_color": COLORS["accent"], "hover_color": COLORS["accent_hover"], "text_color": "white"},
            "secondary": {"fg_color": COLORS["card"], "hover_color": COLORS["glass_edge"], "border_width": 1, "border_color": COLORS["border"], "text_color": COLORS["text"]},
            "danger": {"fg_color": "#2a0a0a", "hover_color": "#3a1515", "border_width": 1, "border_color": COLORS["danger"], "text_color": COLORS["danger"]},
            "tinted": {"fg_color": "#1e1b4b", "hover_color": "#312e81", "text_color": COLORS["accent"], "border_width": 0},
        }

        # --- WINDOW SIZING: resizable, default 1100x720, min 800x520 ---
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        win_width = min(1100, max(800, int(screen_width * 0.92)))
        win_height = min(720, max(520, int(screen_height * 0.88)))

        # --- WINDOW SETUP ---
        admin_title = "  \u2022  Administrator" if self.is_admin else ""
        self.title(f"Ombra Utility v3.0{admin_title}")
        self.geometry(f"{win_width}x{win_height}")
        self.configure(fg_color=COLORS["bg"])
        self.resizable(True, True)
        self.minsize(800, 520)
        self._set_window_icon()

        # --- LAYOUT: top-bar nav + content area ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # row 0 = nav bar, row 1 = content

        # --- SPLASH: full-window overlay ---
        splash_frame = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0, border_width=0)
        splash_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        splash_frame.grid_rowconfigure(0, weight=1)
        splash_frame.grid_columnconfigure(0, weight=1)
        splash_inner = ctk.CTkFrame(splash_frame, fg_color="transparent", width=420, height=200)
        splash_inner.place(relx=0.5, rely=0.5, anchor="center")
        splash_inner.pack_propagate(False)
        ctk.CTkLabel(splash_inner, text="OMBRA", font=("Segoe UI Variable Display", 32, "bold"), text_color=COLORS["text"]).pack(pady=(20, 2))
        ctk.CTkLabel(splash_inner, text="Utility Pro", font=("Segoe UI", 13), text_color=COLORS["subtext"]).pack(pady=(0, 20))
        splash_progress = ctk.CTkProgressBar(splash_inner, height=4, corner_radius=2, progress_color=COLORS["accent"], fg_color=COLORS["border"], mode="determinate", width=300)
        splash_progress.pack(pady=(0, 8))
        splash_status = ctk.CTkLabel(splash_inner, text="Starting...", font=("Segoe UI", 11), text_color=COLORS["subtext"])
        splash_status.pack(pady=(0, 6))
        splash_progress.set(0)
        self.deiconify()
        self.update_idletasks()
        self.update()
        _splash_start = time.time()
        SPLASH_MIN_SEC = 1.8

        SPLASH_TOTAL = 100
        splash_done = [0]

        def _splash_step(weight, msg):
            splash_done[0] = min(SPLASH_TOTAL, splash_done[0] + weight)
            pct = splash_done[0] / SPLASH_TOTAL
            splash_progress.set(pct)
            splash_status.configure(text=msg)

        nav_items = ["Home", "Install", "Tools", "Scan", "System", "Settings", "Logs"]
        self.load_config()
        _splash_step(3, "Loading config...")

        # --- TOP NAV BAR ---
        self.nav_frame = ctk.CTkFrame(self, height=52, corner_radius=0, fg_color=COLORS["bg"], border_width=0)
        self.nav_frame.grid(row=0, column=0, sticky="ew")
        self.nav_frame.grid_propagate(False)
        nav_border = ctk.CTkFrame(self.nav_frame, height=1, fg_color=COLORS["border"])
        nav_border.pack(side="bottom", fill="x")
        nav_inner = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
        nav_inner.pack(fill="both", expand=True, padx=16)
        # Logo (left, not clickable as nav)
        logo_frame = ctk.CTkFrame(nav_inner, fg_color="transparent")
        logo_frame.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(logo_frame, text="OMBRA", font=("Segoe UI Variable Display", 16, "bold"), text_color=COLORS["text"]).pack(side="left")
        if self.is_admin:
            ctk.CTkLabel(logo_frame, text="  \u25CF", font=("Segoe UI", 10), text_color=COLORS["success"]).pack(side="left", padx=(4, 0))
        # Nav pill container
        pill_frame = ctk.CTkFrame(nav_inner, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"], height=36)
        pill_frame.pack(side="left", pady=8)
        self.nav_buttons = {}
        splash_frame.lift()
        for name in nav_items:
            btn = ctk.CTkButton(pill_frame, text=name, height=32, width=0,
                                font=("Segoe UI", 12, "bold"), corner_radius=10,
                                fg_color="transparent", hover_color=COLORS["hover"],
                                text_color=COLORS["subtext"], border_width=0,
                                command=lambda n=name: self.show_frame(n))
            btn.pack(side="left", padx=2, pady=2)
            self.nav_buttons[name] = btn
        # Version + admin button (right side)
        right_frame = ctk.CTkFrame(nav_inner, fg_color="transparent")
        right_frame.pack(side="right")
        ctk.CTkLabel(right_frame, text="v3.0", font=("Segoe UI", 10), text_color=COLORS["glass_edge"]).pack(side="left", padx=(0, 8))
        if self.is_admin:
            admin_badge = ctk.CTkLabel(right_frame, text="\U0001F6E1 Admin", font=("Segoe UI", 10, "bold"),
                                       text_color=COLORS["success"], fg_color=COLORS["card"],
                                       corner_radius=6, height=26, padx=8)
            admin_badge.pack(side="left")
        else:
            ctk.CTkButton(right_frame, text="\U0001F6E1 Run as Admin", height=28, width=100, corner_radius=8,
                          font=("Segoe UI", 11, "bold"), fg_color=COLORS["accent"],
                          hover_color=COLORS["accent_hover"], text_color="white",
                          border_width=0,
                          command=lambda: run_as_admin(getattr(self, "_current_page", "Home"))).pack(side="left")
        _splash_step(10, "Building interface...")

        # --- CONTENT FRAMES ---
        self.content_area = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content_area.grid(row=1, column=0, sticky="nsew", padx=24, pady=(16, 16))
        self.content_frames = {}
        for name in nav_items:
            frame = ctk.CTkFrame(self.content_area, fg_color="transparent", corner_radius=0)
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            if name != "Home":
                ctk.CTkLabel(frame, text="Loading...", font=("Segoe UI", 13), text_color=COLORS["subtext"]).place(relx=0.5, rely=0.5, anchor="center")
            self.content_frames[name] = frame
        splash_frame.lift()
        self.update_idletasks()
        self.update()
        self._frame_built = set()
        self._builders = {
            "Home": self.build_dashboard_frame,
            "System": self.build_sysinfo_frame,
            "Install": self.build_installer_frame,
            "Tools": self.build_tools_frame,
            "Scan": self.build_file_scanner_frame,
            "Settings": self.build_settings_frame,
            "Logs": self.build_logs_frame,
        }
        # Start installer list preload early
        if is_winget_available():
            def _installer_preload_worker():
                self.installed_software_ids = check_installed_software()
                self._installer_preload_done = True
            self._installer_preload_thread = threading.Thread(target=_installer_preload_worker, daemon=True)
            self._installer_preload_thread.start()
        else:
            self._installer_preload_thread = None
        _splash_step(4, "Preloading fonts...")
        splash_frame.lift()
        self._preload_fonts()
        _splash_step(5, "Loading Home...")
        self._frame_built.add("Home")
        self.build_dashboard_frame()
        self._deferred_setup_graph()
        splash_frame.lift()
        self.update_idletasks()
        self.update()
        _splash_step(18, "Loading Tools...")
        self._frame_built.add("Tools")
        self.build_tools_frame()
        _splash_step(12, "Loading Scan...")
        self._frame_built.add("Scan")
        self.build_file_scanner_frame()
        _splash_step(10, "Loading Install...")
        splash_frame.lift()
        self.update_idletasks()
        self.update()
        if getattr(self, "_installer_preload_thread", None) is not None:
            self._installer_preload_thread.join(timeout=60)
        self._frame_built.add("Install")
        self.build_installer_frame()
        _splash_step(8, "Loading System...")
        self._frame_built.add("System")
        self.build_sysinfo_frame()
        _splash_step(4, "Loading Settings...")
        self._frame_built.add("Settings")
        self.build_settings_frame()
        _splash_step(2, "Loading Logs...")
        self._frame_built.add("Logs")
        self.build_logs_frame()
        _splash_step(2, "Finalizing...")
        self.update_vitals()
        self.update_dashboard_extras()
        self.setup_observer()
        self.bind("<Configure>", self._on_window_resize)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        _splash_step(SPLASH_TOTAL - splash_done[0], "Ready!")
        splash_progress.set(1.0)
        splash_frame.lift()
        self.update_idletasks()
        self.update()
        restore_page = "Home"
        for arg in sys.argv[1:]:
            if arg.startswith("--restore-page="):
                pg = arg.split("=", 1)[1]
                if pg in self.content_frames:
                    restore_page = pg
        self.show_frame(restore_page)
        self.content_frames[restore_page].tkraise()
        splash_frame.lift()
        self.update_idletasks()
        self.update()

        def _remove_splash():
            try:
                if not self.winfo_exists():
                    return
            except tk.TclError:
                return
            elapsed = time.time() - _splash_start
            if elapsed < SPLASH_MIN_SEC:
                try:
                    self.after(int((SPLASH_MIN_SEC - elapsed) * 1000), _remove_splash)
                except tk.TclError:
                    pass
                return
            try:
                splash_frame.place_forget()
                splash_frame.grid_remove()
                pg = getattr(self, "_current_page", "Home")
                self.content_frames[pg].tkraise()
                self.lift()
                self.focus_force()
            except (tk.TclError, Exception):
                pass

        self.after(400, _remove_splash)

    def _preload_fonts(self):
        """Warm the font cache so first use of each font doesn't cause a stall."""
        try:
            warm = ctk.CTkFrame(self, fg_color="transparent", width=1, height=1)
            warm.place(x=-1000, y=-1000)
            for spec in _PRELOAD_FONTS:
                font = (spec[0], spec[1]) if len(spec) == 2 else (spec[0], spec[1], spec[2])
                ctk.CTkLabel(warm, text="0", font=font).pack()
            self.update_idletasks()
            warm.destroy()
        except Exception:
            pass

    def _preload_next_tab(self):
        """Build one lazy tab in the background so it's ready when the user clicks."""
        for name in _PRELOAD_TABS:
            if name not in self._frame_built:
                self._frame_built.add(name)
                try:
                    self._builders[name]()
                except Exception:
                    self._frame_built.discard(name)
                self.after(400, self._preload_next_tab)
                return

    def debounce_sort(self):
        if self.sort_timer:
            self.after_cancel(self.sort_timer)
        self.sort_timer = self.after(1500, self.perform_sort)

    def show_frame(self, name):
        """Raises the selected frame immediately; builds content on first visit (next tick) so nav feels instant."""
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        self._current_page = name
        for frame_name, frame in self.content_frames.items():
            if frame_name == name:
                frame.tkraise()
                self.nav_buttons[frame_name].configure(fg_color=COLORS["accent"], text_color="white")
            else:
                self.nav_buttons[frame_name].configure(fg_color="transparent", text_color=COLORS["subtext"])
        if name not in self._frame_built:
            self._frame_built.add(name)
            self.after(0, self._builders[name])

    def log_message(self, message, level="INFO"):
        """Safely logs a message to the UI log area and console."""
        print(f"[{level}] {message}") # Console
        self.after(0, self._safe_log, message, level)

    def _safe_log(self, message, level):
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        if not getattr(self, "log_area", None) or not self.log_area.winfo_exists():
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        try:
            self._log_configure_tags_once()
            line = f"{timestamp} [{level}] {message}\n"
            self.log_area.insert("1.0", line, level)
            if int(self.log_area.index("end-1c").split(".")[0]) > 500:
                self.log_area.delete("500.0", "end")
        except (tk.TclError, AttributeError):
            pass

    def _get_resource_path(self, filename):
        """Path to a bundled file (icon etc.). Works when run as script or as PyInstaller exe."""
        if getattr(sys, "frozen", False):
            return os.path.join(sys._MEIPASS, filename)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    def _get_hwnd(self):
        """Return the Windows HWND for this window (for icon/API)."""
        if platform.system() != "Windows":
            return None
        try:
            h = ctypes.windll.user32.GetParent(self.winfo_id())
            return h if h else self.winfo_id()
        except Exception:
            return None

    def _set_window_icon(self):
        """Set the window/taskbar icon. Uses icon.ico with multiple sizes (title bar + taskbar)."""
        if platform.system() != "Windows":
            return
        icon_path = self._get_resource_path("icon.ico")
        if not os.path.isfile(icon_path):
            return
        try:
            self.iconbitmap(icon_path)
        except Exception:
            pass
        self.after(150, lambda: self._apply_win32_icon(icon_path))

    def _apply_win32_icon(self, icon_path):
        """Set ICON_SMALL (title bar) and ICON_BIG (taskbar/alt-tab) from icon.ico."""
        if platform.system() != "Windows" or not os.path.isfile(icon_path):
            return
        try:
            hwnd = self._get_hwnd()
            if not hwnd:
                return
            IMAGE_ICON = 1
            LR_LOADFROMFILE = 0x10
            WM_SETICON = 0x80
            ICON_SMALL = 0
            ICON_BIG = 1
            SM_CXSMICON = 49
            SM_CYSMICON = 50
            path_w = ctypes.wintypes.LPCWSTR(icon_path)
            cx_sm = ctypes.windll.user32.GetSystemMetrics(SM_CXSMICON)
            cy_sm = ctypes.windll.user32.GetSystemMetrics(SM_CYSMICON)
            # Use 48x48 or 64x64 for taskbar so icon isn't tiny; Windows scales down if needed
            cx_big = 64
            cy_big = 64
            hicon_sm = ctypes.windll.user32.LoadImageW(None, path_w, IMAGE_ICON, cx_sm, cy_sm, LR_LOADFROMFILE)
            hicon_big = ctypes.windll.user32.LoadImageW(None, path_w, IMAGE_ICON, cx_big, cy_big, LR_LOADFROMFILE)
            if hicon_big:
                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
            if hicon_sm:
                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_sm)
        except Exception:
            pass

    def build_header(self, parent_frame, title, subtitle=""):
        """Builds a consistent header for each content frame."""
        header_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 12))
        title_block = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_block.pack(side="left")
        ctk.CTkLabel(title_block, text=title, font=("Segoe UI Variable Display", 24, "bold")).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(title_block, text=subtitle, font=("Segoe UI", 11), text_color=COLORS["subtext"]).pack(anchor="w", pady=(2, 0))
        ctk.CTkFrame(parent_frame, fg_color=COLORS["border"], height=1).pack(fill="x", pady=(0, 4))

    def build_dashboard_frame(self):
        frame = self.content_frames["Home"]

        # --- LAYOUT ---
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(0, weight=0) # Header
        frame.grid_rowconfigure(1, weight=0) # Graph
        frame.grid_rowconfigure(2, weight=1) # Actions

        # --- HEADER ---
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        title_block = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_block.pack(side="left")
        ctk.CTkLabel(title_block, text="Dashboard", font=("Segoe UI Variable Display", 24, "bold")).pack(anchor="w")
        ctk.CTkLabel(title_block, text="Real-time system overview", font=("Segoe UI", 11), text_color=COLORS["subtext"]).pack(anchor="w", pady=(2, 0))
        self.status_bar = ctk.CTkLabel(header_frame, text="  \u25CF  System OK  ", font=("Segoe UI", 10, "bold"),
                                 fg_color=COLORS["card"], height=26, corner_radius=8, text_color=COLORS["success"])
        self.status_bar.pack(side="right", padx=10)
        ctk.CTkFrame(frame, fg_color=COLORS["border"], height=1).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(52, 0))

        # --- GRAPH ---
        graph_card = self.create_card(frame)
        graph_card.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self._dashboard_graph_card = graph_card
        self._graph_placeholder = ctk.CTkLabel(graph_card, text="Loading chart...", font=("Segoe UI", 13), text_color=COLORS["subtext"])
        self._graph_placeholder.pack(pady=24, padx=24)

        # --- QUICK ACTIONS ---
        actions_card = self.create_card(frame)
        actions_card.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        self.setup_quick_actions(actions_card)

        # --- SYSTEM INFO & EXTRAS ---
        info_card = self.create_card(frame)
        info_card.grid(row=2, column=1, sticky="nsew", padx=(8, 0))
        self.tabview = ctk.CTkTabview(info_card, fg_color="transparent", segmented_button_fg_color=COLORS["card"],
                                      segmented_button_selected_color=COLORS["accent"], segmented_button_selected_hover_color=COLORS["accent_hover"],
                                      segmented_button_unselected_hover_color=COLORS["glass_edge"],
                                      corner_radius=12)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=5)
        self.tabview.add("Overview")
        self.tabview.add("Storage & Net")
        self.setup_dashboard_overview(self.tabview.tab("Overview"))
        self.setup_dashboard_storage_net(self.tabview.tab("Storage & Net"))

    def setup_graph_widgets(self, parent_card):
        import matplotlib
        matplotlib.use("TkAgg")
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        v_inner = ctk.CTkFrame(parent_card, fg_color="transparent")
        v_inner.pack(pady=(10, 8), padx=15, fill="x")
        self.cpu_label = ctk.CTkLabel(v_inner, text="CPU 0%", font=("Segoe UI Variable Display", 14, "bold"), text_color=COLORS["accent"])
        self.cpu_label.pack(side="left", expand=True)
        self.ram_label = ctk.CTkLabel(v_inner, text="RAM 0%", font=("Segoe UI Variable Display", 14, "bold"), text_color=COLORS["success"])
        self.ram_label.pack(side="left", expand=True)
        self.bat_label = ctk.CTkLabel(v_inner, text="BAT --%", font=("Segoe UI Variable Display", 14, "bold"), text_color=COLORS["warning"])
        self.bat_label.pack(side="right", expand=True)

        self.fig = plt.Figure(figsize=(5, 2), dpi=100)
        self.fig.patch.set_facecolor(COLORS["card"])
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(COLORS["card"])

        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.ax.tick_params(axis='x', colors=COLORS["subtext"], labelsize=8, length=0)
        self.ax.tick_params(axis='y', colors=COLORS["subtext"], labelsize=8, length=0)
        self.ax.set_ylim(0, 100)
        self.ax.set_xlim(0, self.data_points)
        self.ax.set_yticks([0, 25, 50, 75, 100])
        self.ax.set_xticks([])
        self.ax.grid(color=COLORS["border"], linestyle='-', linewidth=0.4, axis='y', alpha=0.6)
        self.fig.tight_layout(pad=0.5)

        self.cpu_line, = self.ax.plot(self.cpu_data, color=COLORS["accent"], lw=2.2, label="CPU", alpha=0.9)
        self.ram_line, = self.ax.plot(self.ram_data, color=COLORS["success"], lw=2.2, label="RAM", alpha=0.9)
        self.ax.legend(loc='upper left', frameon=False, fontsize=9, labelcolor=COLORS['text'], ncol=2)

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent_card)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="x", padx=10, pady=(0, 5))

    def _deferred_setup_graph(self):
        """Runs one tick after dashboard build so the window paints first without waiting for matplotlib."""
        try:
            if getattr(self, "_graph_placeholder", None) and self._graph_placeholder.winfo_exists():
                self._graph_placeholder.destroy()
                self._graph_placeholder = None
            if getattr(self, "_dashboard_graph_card", None):
                self.setup_graph_widgets(self._dashboard_graph_card)
        except Exception:
            pass

    def setup_quick_actions(self, actions_card):
        self._build_card_header(actions_card, "Quick Actions", "One-tap from your dashboard", COLORS["accent"])
        self._tool_row(actions_card, "Clean Desktop Now", self.perform_sort, "\U0001F4C1")
        self._tool_row(actions_card, "Flush DNS Cache", self.flush_dns, "\U0001F310")
        self._tool_row(actions_card, "Empty Recycle Bin", self.empty_recycle_bin, "\U0001F5D1")
        self._tool_row(actions_card, "Task Manager", lambda: self.open_sys_tool("taskmgr"), "\U0001F4CA")
        self._tool_row(actions_card, "Check for Updates", lambda: self.open_shell_command("start ms-settings:windowsupdate"), "\U0001F504")
        ctk.CTkFrame(actions_card, height=6, fg_color="transparent").pack()

    def setup_dashboard_overview(self, parent):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="both", expand=True)
        wrap.configure(height=260)
        wrap.pack_propagate(False)
        _ov_icons = {"OS": "\U0001F5A5", "CPU": "\u2699", "RAM": "\U0001F4BE", "Uptime": "\u23F1"}
        _ov_accents = {"OS": COLORS["accent"], "CPU": COLORS["warning"], "RAM": COLORS["success"], "Uptime": COLORS["subtext"]}
        self._overview_value_labels = {}
        for key in ("OS", "CPU", "RAM", "Uptime"):
            row = ctk.CTkFrame(wrap, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkFrame(row, width=3, height=14, fg_color=_ov_accents[key], corner_radius=2).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row, text=_ov_icons[key], font=("Segoe UI", 12), width=20).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(row, text=key, font=("Segoe UI", 12, "bold"), text_color=COLORS["subtext"], width=60, anchor="w").pack(side="left")
            val_label = ctk.CTkLabel(row, text="Loading\u2026", font=("Segoe UI", 12), anchor="w", text_color=COLORS["subtext"])
            val_label.pack(side="left", fill="x", expand=True)
            self._overview_value_labels[key] = val_label
        try:
            info = self._gather_system_info_impl()
            uptime = self.get_uptime()
            self._apply_dashboard_overview(info, uptime)
        except Exception:
            pass

    def _apply_dashboard_overview(self, sys_info, uptime):
        if not getattr(self, "_overview_value_labels", None):
            return
        labels = self._overview_value_labels
        for key, value in [("OS", sys_info["os"]), ("CPU", sys_info["cpu"]), ("RAM", sys_info["ram"]), ("Uptime", uptime)]:
            if key in labels and labels[key].winfo_exists():
                labels[key].configure(text=value, text_color=COLORS["text"])
        self._system_info_cache = sys_info

    def setup_dashboard_storage_net(self, parent):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="both", expand=True)
        wrap.configure(height=260)
        wrap.pack_propagate(False)
        # Disk Usage
        disk_hdr = ctk.CTkFrame(wrap, fg_color="transparent")
        disk_hdr.pack(fill="x", pady=(10, 6))
        ctk.CTkFrame(disk_hdr, width=3, height=14, fg_color=COLORS["accent"], corner_radius=2).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(disk_hdr, text="\U0001F4BF", font=("Segoe UI", 12), width=20).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(disk_hdr, text="Disk Usage (C:)", font=("Segoe UI", 12, "bold")).pack(side="left")
        self.disk_bar = ctk.CTkProgressBar(wrap, height=10, corner_radius=5, progress_color=COLORS["accent"], fg_color=COLORS["border"])
        self.disk_bar.pack(fill="x", pady=(0, 4))
        self.disk_label = ctk.CTkLabel(wrap, text="Calculating\u2026", font=("Segoe UI", 11), text_color=COLORS["subtext"])
        self.disk_label.pack(anchor="e")

        # Network Latency
        net_hdr = ctk.CTkFrame(wrap, fg_color="transparent")
        net_hdr.pack(fill="x", pady=(14, 6))
        ctk.CTkFrame(net_hdr, width=3, height=14, fg_color=COLORS["success"], corner_radius=2).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(net_hdr, text="\U0001F310", font=("Segoe UI", 12), width=20).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(net_hdr, text="Network Latency (8.8.8.8)", font=("Segoe UI", 12, "bold")).pack(side="left")
        self.ping_label = ctk.CTkLabel(wrap, text="-- ms", font=("Segoe UI Variable Display", 22, "bold"), text_color=COLORS["success"])
        self.ping_label.pack(anchor="center", pady=8)

    def update_dashboard_extras(self):
        """Run disk and ping in background threads so UI never blocks."""
        def _disk():
            try:
                usage = shutil.disk_usage("C:\\")
                pct = usage.used / usage.total
                total_gb = usage.total // (1024**3)
                self.after(0, lambda: self._apply_disk_ui(pct, total_gb))
            except Exception:
                pass
        def _ping():
            try:
                t1 = time.time()
                socket.create_connection(("8.8.8.8", 53), timeout=2).close()
                latency = int((time.time() - t1) * 1000)
                if latency < 1:
                    latency = 1
                color = COLORS["success"] if latency < 50 else COLORS["warning"] if latency < 150 else COLORS["danger"]
                self.after(0, lambda: self.ping_label.configure(text=f"{latency} ms", text_color=color))
            except Exception:
                self.after(0, lambda: self.ping_label.configure(text="Timeout", text_color="red"))
        if getattr(self, "disk_bar", None) and self.disk_bar.winfo_exists():
            threading.Thread(target=_disk, daemon=True).start()
        if getattr(self, "ping_label", None) and self.ping_label.winfo_exists():
            if self.ping_thread is None or not self.ping_thread.is_alive():
                self.ping_thread = threading.Thread(target=_ping, daemon=True)
                self.ping_thread.start()
        self.after(5000, self.update_dashboard_extras)

    def _apply_disk_ui(self, percent, total_gb):
        try:
            self.disk_bar.set(percent)
            self.disk_label.configure(text=f"{percent*100:.1f}% Used of {total_gb} GB")
        except Exception:
            pass

    def get_uptime(self):
        try:
            delta = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
            return str(delta).split('.')[0] # Remove microseconds
        except: return "Unknown"


    def build_sysinfo_frame(self):
        frame = self.content_frames["System"]
        for w in frame.winfo_children():
            w.destroy()
        self.build_header(frame, "System Information", "Hardware and software details for this machine")

        scroll_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent",
                                              scrollbar_fg_color=COLORS["bg"],
                                              scrollbar_button_color=COLORS["border"], scrollbar_button_hover_color=COLORS["glass_edge"])
        self._style_scrollable(scroll_frame)
        scroll_frame.pack(fill="both", expand=True, padx=10)
        self._sysinfo_scroll_frame = scroll_frame
        placeholder = self.create_card(scroll_frame)
        placeholder.pack(fill="x", pady=8, padx=10)
        ctk.CTkLabel(placeholder, text="Loading system info…", font=("Segoe UI", 14), text_color=COLORS["subtext"]).pack(padx=20, pady=15)
        self._sysinfo_placeholder = placeholder
        if self._system_info_cache is not None:
            placeholder.destroy()
            self._sysinfo_placeholder = None
            self._populate_sysinfo_cards(self._system_info_cache)
        else:
            def _load():
                info = self._gather_system_info_impl()
                self.after(0, self._populate_sysinfo_cards, info)
            threading.Thread(target=_load, daemon=True).start()

    def _populate_sysinfo_cards(self, sys_info):
        if not getattr(self, "_sysinfo_scroll_frame", None):
            return
        sf = self._sysinfo_scroll_frame
        if getattr(self, "_sysinfo_placeholder", None) and self._sysinfo_placeholder.winfo_exists():
            self._sysinfo_placeholder.destroy()
        self._system_info_cache = sys_info
        info_list = [
            ("\U0001F4BB", "Hostname", sys_info["hostname"], COLORS["accent"]),
            ("\U0001F5A5", "Operating System", sys_info["os_full"], COLORS["success"]),
            ("\u2699", "CPU Model", sys_info["cpu"], COLORS["warning"]),
            ("\U0001F4BE", "Total RAM", sys_info["ram"], COLORS["accent"]),
            ("\U0001F40D", "Python Version", sys_info["python_version"], COLORS["success"]),
        ]
        for icon, label, value, ac in info_list:
            card = self.create_card(sf)
            card.pack(fill="x", pady=4, padx=10)
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=12)
            ctk.CTkFrame(row, width=3, height=16, fg_color=ac, corner_radius=2).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(row, text=icon, font=("Segoe UI", 14), width=24).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row, text=label, font=("Segoe UI", 12), text_color=COLORS["subtext"]).pack(side="left")
            ctk.CTkLabel(row, text=value, font=("Segoe UI", 12, "bold"), text_color=COLORS["text"]).pack(side="right")

    def build_installer_frame(self):
        frame = self.content_frames["Install"]
        for w in frame.winfo_children():
            w.destroy()
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        self.build_header(frame, "Install", "Install apps via Windows Package Manager (winget)")

        if not is_winget_available():
            msg_card = self.create_card(frame)
            msg_card.pack(fill="both", expand=True)
            self._build_card_header(msg_card, "Winget Not Found", "Package manager is required", COLORS["warning"])
            ctk.CTkLabel(msg_card, text="Install App Installer from the Microsoft Store\nor use Windows 11 to enable winget.",
                         font=("Segoe UI", 12), text_color=COLORS["subtext"], wraplength=400, justify="center").pack(pady=(4, 14), padx=20)
            def _open_app_installer_store():
                try:
                    import webbrowser
                    webbrowser.open(WINGET_APP_INSTALLER_STORE_URL)
                except Exception:
                    pass
            get_winget_btn = self.create_button(msg_card, "Get App Installer (Microsoft Store)", "primary", _open_app_installer_store)
            get_winget_btn.pack(pady=(0, 20), padx=20)
            self.log_message("Winget not found, installer disabled.", "WARN")
            return

        main_card = self.create_card(frame)
        main_card.pack(fill="both", expand=True)
        main_card.grid_columnconfigure(0, weight=1)
        main_card.grid_rowconfigure(1, weight=1)

        # Top bar: search + refresh
        top_row = ctk.CTkFrame(main_card, fg_color="transparent")
        top_row.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))
        top_row.grid_columnconfigure(0, weight=1)
        self.installer_search = ctk.CTkEntry(top_row, placeholder_text="Search apps...", height=40, corner_radius=12,
                                            fg_color=COLORS["bg"], border_color=COLORS["border"], border_width=1,
                                            font=("Segoe UI", 13), text_color=COLORS["text"])
        self.installer_search.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.installer_search.bind("<KeyRelease>", self._on_installer_search_key)
        self.installer_source_var = ctk.StringVar(value="Winget")
        self.installer_refresh_btn = self.create_button(top_row, "Refresh", "secondary", self._refresh_installer)
        self.installer_refresh_btn.grid(row=0, column=1)

        # Scroll area: search results section (shown when query) + suggested categories
        scroll_frame = ctk.CTkScrollableFrame(main_card, fg_color="transparent",
                                             scrollbar_fg_color=COLORS["card"],
                                             scrollbar_button_color=COLORS["border"],
                                             scrollbar_button_hover_color=COLORS["glass_edge"])
        self._style_scrollable(scroll_frame)
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))
        self.installer_scroll_frame = scroll_frame
        self.installer_category_blocks = []
        # Search results container: created here, packed only when we have a query (packed after categories)
        self._installer_search_results_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        # do not pack yet; pack when showing search results

        if getattr(self, "_installer_preload_done", False):
            self._build_installer_categories()
        else:
            def _populate_installer():
                self.after(0, lambda: self._set_installer_loading(True))
                self.installed_software_ids = check_installed_software()
                self.after(0, lambda: self._set_installer_loading(False))
                self.after(0, self._build_installer_categories)
            threading.Thread(target=_populate_installer, daemon=True).start()

    def _set_installer_loading(self, loading):
        if loading:
            if hasattr(self, "installer_refresh_btn"):
                self.installer_refresh_btn.configure(state="disabled", text="Checking…")
        else:
            if hasattr(self, "installer_refresh_btn"):
                self.installer_refresh_btn.configure(state="normal", text="Refresh")

    def _build_installer_categories(self):
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        if not hasattr(self, "installer_scroll_frame"):
            return
        sf = self.installer_scroll_frame
        search_container = getattr(self, "_installer_search_results_container", None)
        for w in sf.winfo_children():
            if w != search_container:
                w.destroy()
        self.installer_category_blocks.clear()
        self.log_message(f"Found {len(self.installed_software_ids)} installed packages via winget.")
        self._installer_categories_list = list(INSTALLER_CATEGORIES.items())
        self.after(0, self._build_next_installer_category, 0)

    _INSTALLER_CATEGORIES_PER_TICK = 3

    def _build_next_installer_category(self, index):
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        sf = getattr(self, "installer_scroll_frame", None)
        cat_list = getattr(self, "_installer_categories_list", [])
        if not sf or index >= len(cat_list):
            return
        end = min(index + self._INSTALLER_CATEGORIES_PER_TICK, len(cat_list))
        _installer_accent_cycle = [COLORS["accent"], COLORS["success"], COLORS["warning"], COLORS["danger"]]
        for i in range(index, end):
            category, apps = cat_list[i]
            cat_card = self.create_card(sf, corner_radius=16)
            cat_card.pack(fill="x", pady=(14, 0))
            ac = _installer_accent_cycle[i % len(_installer_accent_cycle)]
            self._build_card_header(cat_card, category, f"{len(apps)} apps", ac)
            app_frames = []
            for name, app_id in apps:
                row = ctk.CTkFrame(cat_card, fg_color="transparent")
                row.pack(fill="x", padx=25, pady=(2, 8))
                row.grid_columnconfigure(0, weight=1)
                row.grid_columnconfigure(1, minsize=INSTALLER_ACTION_AREA_WIDTH)
                name_lbl = ctk.CTkLabel(row, text=name, font=("Segoe UI", 14, "bold"), anchor="w")
                name_lbl.grid(row=0, column=0, sticky="w", padx=(0, 12))
                row._installer_name = name
                row._installer_app_id = app_id
                if app_id in self.installed_software_ids:
                    installed_frame = ctk.CTkFrame(row, fg_color="transparent")
                    installed_frame.grid(row=0, column=1, sticky="e")
                    uninstall_btn = self.create_button(installed_frame, "Uninstall", "danger", lambda: None)
                    uninstall_btn.configure(width=INSTALLER_ACTION_BUTTON_WIDTH, command=lambda r=row, id=app_id, n=name: self.uninstall_software(id, "winget", r, n, refresh_search_after=False))
                    uninstall_btn.pack(side="right")
                    ctk.CTkLabel(installed_frame, text="●", font=("Segoe UI", 10), text_color=COLORS["success"]).pack(side="right", padx=(0, 8))
                    row._installer_installed_frame = installed_frame
                else:
                    action_frame = ctk.CTkFrame(row, fg_color="transparent")
                    action_frame.grid(row=0, column=1, sticky="e")
                    status_label = ctk.CTkLabel(action_frame, text="", font=("Segoe UI", 11), text_color=COLORS["subtext"])
                    progress_bar = ctk.CTkProgressBar(action_frame, width=120, height=6, corner_radius=3,
                                                     progress_color=COLORS["accent"], fg_color=COLORS["border"])
                    install_btn = self.create_button(action_frame, "Install", "primary", lambda: None)
                    install_btn.configure(width=INSTALLER_ACTION_BUTTON_WIDTH,
                                          command=lambda af=action_frame, sl=status_label, b=install_btn, pb=progress_bar, wid=app_id: self.install_software(wid, af, sl, b, pb, source="winget"))
                    install_btn.pack(side="right")
                    status_label.pack(side="right", padx=(0, 8))
                app_frames.append(row)
            self.installer_category_blocks.append((cat_card, app_frames))
        if end < len(cat_list):
            self.after(0, self._build_next_installer_category, end)

    def _on_installer_search_key(self, event=None):
        """Filter suggested list and debounce live search."""
        if hasattr(self, "installer_category_blocks"):
            self._filter_installer_apps(event)
        q = (self.installer_search.get() or "").strip()
        if self._installer_search_timer:
            self.after_cancel(self._installer_search_timer)
            self._installer_search_timer = None
        if not q:
            self._installer_search_query_id += 1
            self._hide_installer_search_results()
            return
        self._installer_search_timer = self.after(INSTALLER_SEARCH_DEBOUNCE_MS, self._run_installer_search)

    def _hide_installer_search_results(self):
        if getattr(self, "_installer_search_results_container", None):
            try:
                self._installer_search_results_container.pack_forget()
            except Exception:
                pass
            for w in self._installer_search_results_container.winfo_children():
                w.destroy()

    def _run_installer_search(self):
        self._installer_search_timer = None
        q = (self.installer_search.get() or "").strip()
        if not q:
            self._hide_installer_search_results()
            return
        self._installer_search_query_id += 1
        query_id = self._installer_search_query_id
        source = self.installer_source_var.get() if hasattr(self, "installer_source_var") else "Winget"

        def _worker():
            results = search_winget(q, limit=INSTALLER_SEARCH_LIMIT, timeout_sec=INSTALLER_SEARCH_TIMEOUT)
            installed_winget = check_installed_software()
            self.after(0, lambda: self._apply_installer_search_results(query_id, q, results, installed_winget))

        threading.Thread(target=_worker, daemon=True).start()
        self._show_installer_search_searching()

    def _show_installer_search_searching(self):
        if not getattr(self, "_installer_search_results_container", None):
            return
        for w in self._installer_search_results_container.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._installer_search_results_container, text="Searching…", font=("Segoe UI", 13), text_color=COLORS["subtext"]).pack(pady=20, padx=20)
        self._installer_search_results_container.pack(fill="x", pady=(14, 0))

    def _apply_installer_search_results(self, query_id, query, results, installed_winget):
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        if query_id != self._installer_search_query_id:
            return
        if not getattr(self, "_installer_search_results_container", None):
            return
        for w in self._installer_search_results_container.winfo_children():
            w.destroy()
        # Header
        header = ctk.CTkFrame(self._installer_search_results_container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(header, text=f"Search results for «{query}»", font=("Segoe UI", 14, "bold"), text_color=COLORS["text"]).pack(side="left")
        if not results:
            ctk.CTkLabel(self._installer_search_results_container, text="No results. Try a different search.", font=("Segoe UI", 13), text_color=COLORS["subtext"]).pack(pady=20, padx=20)
            self._installer_search_results_container.pack(fill="x", pady=(14, 0))
            return
        # Result rows (batch in one go; keep list small via INSTALLER_SEARCH_LIMIT)
        card = self.create_card(self._installer_search_results_container, corner_radius=16)
        card.pack(fill="x", pady=(0, 14))
        for pkg in results:
            name, pkg_id, version, src = pkg.get("name", ""), pkg.get("id", ""), pkg.get("version", ""), pkg.get("source", "winget")
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=25, pady=(2, 8))
            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, minsize=INSTALLER_ACTION_AREA_WIDTH)
            label_text = f"{name}  —  {pkg_id}"
            if version:
                label_text += f"  ({version})"
            name_lbl = ctk.CTkLabel(row, text=label_text, font=("Segoe UI", 13, "bold"), anchor="w")
            name_lbl.grid(row=0, column=0, sticky="w", padx=(0, 12))
            is_installed = (src == "winget" and pkg_id in installed_winget)
            row._installer_pkg_id = pkg_id
            row._installer_source = src
            row._installer_name = name
            row._installer_from_search = True
            if is_installed:
                installed_frame = ctk.CTkFrame(row, fg_color="transparent")
                installed_frame.grid(row=0, column=1, sticky="e")
                uninstall_btn = self.create_button(installed_frame, "Uninstall", "danger", lambda: None)
                uninstall_btn.configure(width=INSTALLER_ACTION_BUTTON_WIDTH, command=lambda r=row, id=pkg_id, sr=src, nm=name: self.uninstall_software(id, sr, r, nm, refresh_search_after=True))
                uninstall_btn.pack(side="right")
                ctk.CTkLabel(installed_frame, text="●", font=("Segoe UI", 10), text_color=COLORS["success"]).pack(side="right", padx=(0, 8))
                row._installer_installed_frame = installed_frame
            else:
                action_frame = ctk.CTkFrame(row, fg_color="transparent")
                action_frame.grid(row=0, column=1, sticky="e")
                status_label = ctk.CTkLabel(action_frame, text="", font=("Segoe UI", 11), text_color=COLORS["subtext"])
                progress_bar = ctk.CTkProgressBar(action_frame, width=120, height=6, corner_radius=3,
                                                 progress_color=COLORS["accent"], fg_color=COLORS["border"])
                install_btn = self.create_button(action_frame, "Install", "primary",
                                                 lambda id=pkg_id, af=action_frame, s=status_label, b=None, p=progress_bar, sr=src: self.install_software(id, af, s, b, p, source=sr))
                install_btn.configure(width=INSTALLER_ACTION_BUTTON_WIDTH, command=lambda id=pkg_id, af=action_frame, s=status_label, b=install_btn, p=progress_bar, sr=src: self.install_software(id, af, s, b, p, source=sr))
                install_btn.pack(side="right")
                status_label.pack(side="right", padx=(0, 8))
        self._installer_search_results_container.pack(fill="x", pady=(14, 0))

    def _filter_installer_apps(self, event=None):
        if not hasattr(self, "installer_category_blocks"):
            return
        q = (self.installer_search.get() or "").strip().lower()
        for cat_card, app_frames in self.installer_category_blocks:
            visible = 0
            for row in app_frames:
                name = getattr(row, "_installer_name", "")
                match = not q or q in name.lower()
                if match:
                    row.pack(fill="x", padx=25, pady=(2, 8))
                    visible += 1
                else:
                    row.pack_forget()
            if visible:
                cat_card.pack(fill="x", pady=(14, 0))
            else:
                cat_card.pack_forget()

    def _refresh_installer(self):
        self.installer_search.delete(0, "end")
        self._set_installer_loading(True)
        def _worker():
            self.installed_software_ids = check_installed_software()
            self.after(0, self._build_installer_categories)
            self.after(0, lambda: self._set_installer_loading(False))
        threading.Thread(target=_worker, daemon=True).start()

    def install_software(self, app_id, action_frame, status_label, button, progress_bar, source="winget"):
        """Install via winget."""
        button.pack_forget()
        button.configure(state="disabled")
        status_label.configure(text="Preparing\u2026", text_color=COLORS["accent"])
        progress_bar.set(0)
        progress_bar.pack(side="right", padx=10, fill="x", expand=True)
        self.log_message(f"Starting install for {app_id} (winget)")
        self._install_winget(app_id, action_frame, status_label, button, progress_bar)

    def _install_winget(self, app_id, action_frame, status_label, button, progress_bar):
        """Winget install with progress bar driven by parsed output."""

        install_done = [False]
        progress_timer_id = [None]
        last_parsed_pct = [None]  # when set, bar is driven by winget output instead of timer
        PROGRESS_CAP = 0.98

        # Winget prints e.g. "9.00 MB / 83.2 MB" or "33.2 MB / 83.2 MB" (sometimes with garbage chars)
        re_mb_mb = re.compile(r"(\d+(?:\.\d+)?)\s*MB\s*/\s*(\d+(?:\.\d+)?)\s*MB", re.IGNORECASE)
        re_kb_kb = re.compile(r"(\d+(?:\.\d+)?)\s*KB\s*/\s*(\d+(?:\.\d+)?)\s*KB", re.IGNORECASE)
        re_pct = re.compile(r"(\d{1,3})%")

        def _set_status(text):
            if install_done[0]:
                return
            try:
                self.after(0, lambda t=text: status_label.configure(text=t, text_color=COLORS["accent"]) if status_label.winfo_exists() else None)
            except Exception:
                pass

        def _set_progress(pct):
            if install_done[0]:
                return
            pct = min(1.0, max(0.0, float(pct)))
            last_parsed_pct[0] = pct
            if pct >= 1.0:
                _set_status("Waiting for user…")
            try:
                self.after(0, lambda p=pct: progress_bar.set(p) if progress_bar.winfo_exists() else None)
            except Exception:
                pass

        def _tick():
            if install_done[0]:
                try:
                    if progress_bar.winfo_exists():
                        progress_bar.set(1.0)
                except Exception:
                    pass
                return
            try:
                if not progress_bar.winfo_exists():
                    return
                # If we have real progress from winget, don't advance by timer
                if last_parsed_pct[0] is not None:
                    progress_timer_id[0] = self.after(400, _tick)
                    return
                current = progress_bar.get()
                if current is None or current < 0:
                    current = 0
                progress_bar.set(min(PROGRESS_CAP, current + 0.03))
                progress_timer_id[0] = self.after(400, _tick)
            except Exception:
                pass

        success_reported = [False]
        app_frame = action_frame.master

        def _poll_until_installed():
            """Every few seconds check if app is installed; show Installed as soon as it appears."""
            poll_interval = 2.0
            while not install_done[0]:
                time.sleep(poll_interval)
                if install_done[0]:
                    break
                if is_app_installed(app_id):
                    install_done[0] = True
                    success_reported[0] = True
                    self.after(0, lambda: progress_bar.set(1.0) if progress_bar.winfo_exists() else None)
                    self.after(0, lambda: self.on_install_success(app_frame, action_frame, app_id, "winget"))
                    self.after(0, lambda: self.log_message(f"Detected installed: {app_id}", "SUCCESS"))
                    break

        def _worker():
            poll_thread = threading.Thread(target=_poll_until_installed, daemon=True)
            poll_thread.start()
            start_time = time.time()
            last_stderr_lines = []
            try:
                command = ["winget", "install", "--id", app_id, "-e", "--accept-package-agreements", "--accept-source-agreements"]
                proc = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    bufsize=1,
                )
                last_status = "Preparing…"
                while True:
                    if time.time() - start_time > INSTALLER_INSTALL_TIMEOUT:
                        install_done[0] = True
                        try:
                            proc.kill()
                        except Exception:
                            pass
                        self.after(0, self.on_install_failure, status_label, button, progress_bar)
                        self.log_message("Install timed out. Try again or run as Administrator.", "ERROR")
                        return
                    line = proc.stdout.readline()
                    if not line and proc.poll() is not None:
                        break
                    if not line:
                        continue
                    if line.strip():
                        last_stderr_lines.append(line.strip())
                        if len(last_stderr_lines) > 20:
                            last_stderr_lines.pop(0)
                    line_stripped = line.strip()
                    line_lower = line_stripped.lower()

                    m = re_mb_mb.search(line_stripped)
                    if m:
                        cur, tot = float(m.group(1)), float(m.group(2))
                        if tot > 0:
                            _set_progress(cur / tot)
                    else:
                        m = re_kb_kb.search(line_stripped)
                        if m:
                            cur, tot = float(m.group(1)), float(m.group(2))
                            if tot > 0:
                                _set_progress(cur / tot)
                        else:
                            m = re_pct.search(line_stripped)
                            if m:
                                _set_progress(int(m.group(1)) / 100.0)

                    if "download" in line_lower or "downloading" in line_lower:
                        if last_status != "Downloading…":
                            last_status = "Downloading…"
                            _set_status(last_status)
                    elif "install" in line_lower or "applying" in line_lower or "progress" in line_lower:
                        # Download finished; bar stays at 100%, user may see UAC/installer prompts
                        _set_status("Waiting for user…")
                        _set_progress(1.0)
                install_done[0] = True
                if success_reported[0]:
                    return
                if proc.returncode == 0:
                    self.after(0, lambda: progress_bar.set(1.0) if progress_bar.winfo_exists() else None)
                    self.after(0, lambda: self.on_install_success(app_frame, action_frame, app_id, "winget"))
                    self.log_message(f"Successfully installed {app_id}", "SUCCESS")
                else:
                    err_blob = " ".join(last_stderr_lines[-5:]).lower()
                    if "administrator" in err_blob or "elevated" in err_blob:
                        self.log_message("Install failed. Try running as Administrator.", "ERROR")
                    elif "not found" in err_blob or "no applicable" in err_blob:
                        self.log_message("Package not found or not available.", "ERROR")
                    else:
                        self.log_message(f"Failed to install {app_id}", "ERROR")
                    self.after(0, self.on_install_failure, status_label, button, progress_bar)
            except FileNotFoundError:
                install_done[0] = True
                self.after(0, self.on_install_failure, status_label, button, progress_bar)
                self.log_message("Winget not found. Install App Installer or use Windows 11.", "ERROR")
            except Exception as e:
                install_done[0] = True
                self.after(0, self.on_install_failure, status_label, button, progress_bar)
                self.log_message(f"Install failed: {e}", "ERROR")

        threading.Thread(target=_worker, daemon=True).start()
        progress_timer_id[0] = self.after(400, _tick)
        self.after(1500, lambda: _set_status("Downloading…"))

    def on_install_success(self, app_frame, action_frame, app_id=None, source="winget"):
        """Called on UI thread after successful software installation. If app_id given, adds Uninstall button."""
        if app_id and source == "winget":
            self.installed_software_ids.add(app_id)
        action_frame.destroy()
        installed_frame = ctk.CTkFrame(app_frame, fg_color="transparent")
        installed_frame.grid(row=0, column=1, sticky="e")
        if app_id:
            app_frame._installer_installed_frame = installed_frame
            app_frame._installer_app_id = app_id
            app_frame._installer_source = source
            app_name = getattr(app_frame, "_installer_name", app_id)
            uninstall_btn = self.create_button(installed_frame, "Uninstall", "danger", lambda: None)
            uninstall_btn.configure(width=INSTALLER_ACTION_BUTTON_WIDTH, command=lambda: self.uninstall_software(app_id, source, app_frame, app_name, refresh_search_after=getattr(app_frame, "_installer_from_search", False)))
            uninstall_btn.pack(side="right")
            ctk.CTkLabel(installed_frame, text="●", font=("Segoe UI", 10), text_color=COLORS["success"]).pack(side="right", padx=(0, 8))
        else:
            ctk.CTkLabel(installed_frame, text="●", font=("Segoe UI", 10), text_color=COLORS["success"]).pack(side="right", padx=10)

    def uninstall_software(self, app_id, source, row, app_name=None, refresh_search_after=False):
        """Run uninstall in thread; on success update installed set and refresh row."""
        if not row.winfo_exists():
            return
        src = "winget"
        app_name = app_name or app_id

        def _worker():
            ok, err = uninstall_winget(app_id, timeout_sec=120)
            if ok:
                self.installed_software_ids.discard(app_id)
                self.after(0, lambda: self._installer_row_after_uninstall(row, app_id, app_name, src, refresh_search_after))
                self.log_message(f"Uninstalled {app_name}", "SUCCESS")
            else:
                self.after(0, lambda: self.show_notification(f"Uninstall failed: {err[:80]}", type="error"))
                self.log_message(f"Uninstall failed: {err}", "ERROR")

        threading.Thread(target=_worker, daemon=True).start()

    def _installer_row_after_uninstall(self, row, app_id, app_name, source, refresh_search_after):
        """Replace Installed+Uninstall with Install button on the row."""
        if not getattr(row, "winfo_exists", lambda: False)() or not row.winfo_exists():
            return
        inst_fr = getattr(row, "_installer_installed_frame", None)
        if inst_fr and inst_fr.winfo_exists():
            inst_fr.destroy()
        if hasattr(row, "_installer_installed_frame"):
            delattr(row, "_installer_installed_frame")
        action_frame = ctk.CTkFrame(row, fg_color="transparent")
        action_frame.grid(row=0, column=1, sticky="e")
        status_label = ctk.CTkLabel(action_frame, text="", font=("Segoe UI", 11), text_color=COLORS["subtext"])
        progress_bar = ctk.CTkProgressBar(action_frame, width=120, height=6, corner_radius=3,
                                         progress_color=COLORS["accent"], fg_color=COLORS["border"])
        install_btn = self.create_button(action_frame, "Install", "primary",
                                         lambda id=app_id, af=action_frame, s=status_label, b=None, p=progress_bar, sr=source: self.install_software(id, af, s, b, p, source=sr))
        install_btn.configure(width=INSTALLER_ACTION_BUTTON_WIDTH, command=lambda id=app_id, af=action_frame, s=status_label, b=install_btn, p=progress_bar, sr=source: self.install_software(id, af, s, b, p, source=sr))
        install_btn.pack(side="right")
        status_label.pack(side="right", padx=(0, 8))
        if refresh_search_after and getattr(self, "installer_search", None):
            self.after(300, self._run_installer_search)

    def on_install_failure(self, status_label, button, progress_bar):
        """Called on UI thread after failed software installation."""
        try:
            if progress_bar.winfo_exists():
                progress_bar.set(0)
                progress_bar.pack_forget()
        except Exception:
            pass
        try:
            if status_label.winfo_exists():
                status_label.configure(text="Failed", text_color="red")
        except Exception:
            pass
        try:
            if button.winfo_exists():
                button.pack(side="right")
                button.configure(state="normal")
        except Exception:
            pass

    def build_tools_frame(self):
        frame = self.content_frames["Tools"]
        for w in frame.winfo_children():
            w.destroy()
        self.build_header(frame, "Tools", "Fixes and utilities for everyday IT support")

        # Inline pill selector
        pill_bar = ctk.CTkFrame(frame, fg_color=COLORS["card"], corner_radius=8,
                                border_width=1, border_color=COLORS["border"])
        pill_bar.pack(anchor="w", pady=(0, 6))

        self._tools_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent",
                                                    scrollbar_fg_color=COLORS["bg"],
                                                    scrollbar_button_color=COLORS["border"],
                                                    scrollbar_button_hover_color=COLORS["glass_edge"])
        self._style_scrollable(self._tools_scroll)
        self._tools_scroll.pack(fill="both", expand=True)

        self._tools_tab_frames = {}
        self._tools_pill_btns = {}
        tab_names = ["Quick", "System", "Advanced"]
        for name in tab_names:
            btn = ctk.CTkButton(pill_bar, text=name, height=26, width=0,
                                font=("Segoe UI", 11, "bold"), corner_radius=6,
                                fg_color="transparent", hover_color=COLORS["hover"],
                                text_color=COLORS["subtext"], border_width=0,
                                command=lambda n=name: self._switch_tools_tab(n))
            btn.pack(side="left", padx=2, pady=3)
            self._tools_pill_btns[name] = btn
            tab_frame = ctk.CTkFrame(self._tools_scroll, fg_color="transparent")
            self._tools_tab_frames[name] = tab_frame

        self._tools_active_tab = None
        self.after(0, self._build_tools_tabs_deferred, 0)

    def _switch_tools_tab(self, name):
        if self._tools_active_tab == name:
            return
        self._tools_active_tab = name
        for n, btn in self._tools_pill_btns.items():
            if n == name:
                btn.configure(fg_color=COLORS["accent"], text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["subtext"])
        for n, f in self._tools_tab_frames.items():
            if n == name:
                f.pack(fill="both", expand=True)
            else:
                f.pack_forget()

    _TOOLS_TABS_PER_TICK = 2

    def _build_tools_tabs_deferred(self, index):
        builders = [
            ("Quick", self._build_tools_quick_tab),
            ("System", self._build_tools_system_tab),
            ("Advanced", self._build_tools_advanced_tab),
        ]
        end = min(index + self._TOOLS_TABS_PER_TICK, len(builders))
        for i in range(index, end):
            name, build_fn = builders[i]
            build_fn(self._tools_tab_frames[name])
        if end < len(builders):
            self.after(0, self._build_tools_tabs_deferred, end)
        else:
            self._switch_tools_tab("Quick")

    def _create_tools_tab_scroller(self, parent_tab):
        wrapper = ctk.CTkFrame(parent_tab, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=4, pady=4)
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_columnconfigure(1, weight=1)
        return wrapper

    def _build_tools_quick_tab(self, tab):
        scroll_frame = self._create_tools_tab_scroller(tab)
        tr = self._tool_row

        # --- Folder Cleanup ---
        c1 = self.create_card(scroll_frame)
        c1.grid(row=0, column=0, padx=(0, 6), pady=6, sticky="nsew")
        self._build_card_header(c1, "Folder Cleanup", "Auto-sort files into organized folders", COLORS["accent"])
        tr(c1, "Clean Desktop", self.perform_sort, "\U0001F4C1")
        tr(c1, "Clean Downloads", self.perform_downloads_sort, "\U0001F4C2")
        ctk.CTkFrame(c1, fg_color=COLORS["border"], height=1).pack(fill="x", padx=16, pady=4)
        rt_frame = ctk.CTkFrame(c1, fg_color="transparent")
        rt_frame.pack(fill="x", padx=16, pady=(2, 4))
        rt_left = ctk.CTkFrame(rt_frame, fg_color="transparent")
        rt_left.pack(side="left")
        ctk.CTkLabel(rt_left, text="Auto-Clean Desktop", font=("Segoe UI", 11, "bold"), text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(rt_left, text="Sort new files automatically", font=("Segoe UI", 10), text_color=COLORS["subtext"]).pack(anchor="w")
        self.realtime_switch = ctk.CTkSwitch(rt_frame, text="", width=42, height=22, command=self.toggle_realtime_sort,
                                             progress_color=COLORS["accent"], button_color=COLORS["glass_edge"],
                                             fg_color=COLORS["border"], button_hover_color=COLORS["accent_hover"])
        self.realtime_switch.pack(side="right")
        ctk.CTkFrame(c1, fg_color=COLORS["border"], height=1).pack(fill="x", padx=16, pady=4)
        self.btn_hide = tr(c1, "Incognito: Hide Icons", self.toggle_icons, "\U0001F441")
        tr(c1, "Purge Clipboard", self.purge_clip, "\U0001F4CB")
        ctk.CTkFrame(c1, height=6, fg_color="transparent").pack()

        # --- System Cleanup ---
        c2 = self.create_card(scroll_frame)
        c2.grid(row=0, column=1, padx=(6, 0), pady=6, sticky="nsew")
        self._build_card_header(c2, "System Cleanup", "Free space and fix sign-in issues", COLORS["success"])
        tr(c2, "Clean Temp Files", self.clean_temp_files, "\U0001F9F9", admin=True)
        tr(c2, "Reset M365 Credentials", self.clean_m365_credentials, "\U0001F512", admin=True)
        tr(c2, "Clear Thumbnail Cache", self.clear_thumbnail_cache, "\U0001F5BC")
        tr(c2, "Storage Sense", lambda: self.open_shell_command("start ms-settings:storagestorage"), "\U0001F4BE")
        ctk.CTkFrame(c2, height=6, fg_color="transparent").pack()

        # --- Cache & Recycle Bin ---
        c3 = self.create_card(scroll_frame)
        c3.grid(row=1, column=0, padx=(0, 6), pady=6, sticky="nsew")
        self._build_card_header(c3, "Cache & Recycle Bin", "Clear caches and free storage", COLORS["warning"])
        tr(c3, "Clear Update Cache", self.clear_update_cache, "\U0001F504", admin=True)
        tr(c3, "Clear Delivery Optimization", self.clear_delivery_optimization, "\U0001F4E6", admin=True)
        tr(c3, "Clear Error Reports", self.clear_windows_error_reports, "\U0001F4DD", admin=True)
        tr(c3, "Clear Icon Cache", self.clear_icon_cache, "\U0001F3A8", admin=True)
        tr(c3, "Clear Prefetch", self.clear_prefetch, "\u26A1", admin=True)
        tr(c3, "Empty Recycle Bin", self.empty_recycle_bin, "\U0001F5D1")
        tr(c3, "Clear Browser Cache", self.clear_browser_cache, "\U0001F310")
        ctk.CTkFrame(c3, height=6, fg_color="transparent").pack()

        # --- Network Fixes ---
        c4 = self.create_card(scroll_frame)
        c4.grid(row=1, column=1, padx=(6, 0), pady=6, sticky="nsew")
        self._build_card_header(c4, "Network Fixes", "Quick connectivity fixes", COLORS["accent"])
        tr(c4, "Flush DNS Cache", self.flush_dns, "\U0001F310", admin=True)
        tr(c4, "Reset Winsock", self.reset_winsock, "\U0001F50C", admin=True)
        tr(c4, "Reset Network Stack", self.reset_network_stack, "\U0001F4E1", admin=True)
        tr(c4, "Release & Renew IP", self.release_renew_ip, "\U0001F504", admin=True)
        ctk.CTkFrame(c4, height=6, fg_color="transparent").pack()

    def _build_tools_system_tab(self, tab):
        scroll_frame = self._create_tools_tab_scroller(tab)
        tr = self._tool_row

        # --- Repair & Maintenance ---
        c1 = self.create_card(scroll_frame)
        c1.grid(row=0, column=0, padx=(0, 6), pady=6, sticky="nsew")
        self._build_card_header(c1, "Repair & Maintenance", "Scan and repair system files", COLORS["danger"])
        tr(c1, "System File Checker (SFC)", self.run_sfc_scan, "\U0001F6E0", admin=True)
        tr(c1, "Repair Windows Image (DISM)", self.run_dism_scan, "\U0001F527", admin=True)
        tr(c1, "Create Restore Point", self.create_restore_point, "\U0001F4BE", admin=True)
        tr(c1, "Check Disk (Read-Only)", lambda: self.open_shell_command("start cmd /k chkdsk C:"), "\U0001F4BF")
        tr(c1, "Disk Management", lambda: self.open_sys_tool("diskmgmt.msc"), "\U0001F4BD")
        tr(c1, "Disk Cleanup", self.run_disk_cleanup, "\U0001F9F9")
        tr(c1, "Sync Windows Time", self.sync_time_windows, "\U0001F552", admin=True)
        ctk.CTkFrame(c1, height=6, fg_color="transparent").pack()

        # --- Power Management ---
        c2 = self.create_card(scroll_frame)
        c2.grid(row=0, column=1, padx=(6, 0), pady=6, sticky="nsew")
        self._build_card_header(c2, "Power Management", "Battery, shutdown, and hibernation", COLORS["warning"])
        tr(c2, "Battery Report", self.generate_battery_report, "\U0001F50B")
        tr(c2, "Schedule Shutdown (1h)", lambda: self.schedule_shutdown(3600), "\u23F0")
        tr(c2, "Abort Shutdown", lambda: self.run_command(["shutdown", "/a"], "Shutdown Cancelled"), "\u26D4")
        tr(c2, "Disable Hibernation", lambda: self.run_command(["powercfg.exe", "/hibernate", "off"], "Hibernation Disabled"), "\U0001F4A4", admin=True)
        tr(c2, "Enable Hibernation", lambda: self.run_command(["powercfg.exe", "/hibernate", "on"], "Hibernation Enabled"), "\U0001F4A4", admin=True)
        tr(c2, "Turn Off Monitor", self.turn_off_monitor, "\U0001F4BB")
        ctk.CTkFrame(c2, height=6, fg_color="transparent").pack()

        # --- Processes & Services ---
        c3 = self.create_card(scroll_frame)
        c3.grid(row=1, column=0, padx=(0, 6), pady=6, sticky="nsew")
        self._build_card_header(c3, "Processes & Services", "Restart stuck services", COLORS["accent"])
        tr(c3, "Restart Print Spooler", self.restart_spooler, "\U0001F5A8", admin=True)
        tr(c3, "Restart Audio Service", self.restart_audio_service, "\U0001F50A", admin=True)
        tr(c3, "Restart Explorer.exe", self.restart_explorer, "\U0001F4C1", admin=True)
        tr(c3, "Task Scheduler", self.open_task_scheduler, "\U0001F4C5")
        tr(c3, "Reliability Monitor", self.reliability_monitor, "\U0001F4CA")
        ctk.CTkFrame(c3, height=6, fg_color="transparent").pack()

        # --- Windows Settings ---
        c4 = self.create_card(scroll_frame)
        c4.grid(row=1, column=1, padx=(6, 0), pady=6, sticky="nsew")
        self._build_card_header(c4, "Windows Settings", "Quick links to settings pages", COLORS["success"])
        tr(c4, "Windows Updates", lambda: self.open_shell_command("start ms-settings:windowsupdate"), "\U0001F504")
        tr(c4, "Startup Apps", lambda: self.open_shell_command("start ms-settings:startupapps"), "\U0001F680")
        tr(c4, "Windows Security", lambda: self.open_shell_command("start ms-settings:windowsdefender"), "\U0001F6E1")
        tr(c4, "Sound", lambda: self.open_shell_command("start ms-settings:sound"), "\U0001F50A")
        tr(c4, "Display", lambda: self.open_shell_command("start ms-settings:display"), "\U0001F5A5")
        tr(c4, "Storage", lambda: self.open_shell_command("start ms-settings:storagestorage"), "\U0001F4BE")
        tr(c4, "Optional Features", lambda: self.open_shell_command("start ms-settings:optionalfeatures"), "\u2699")
        tr(c4, "Default Apps", lambda: self.open_shell_command("start ms-settings:defaultapps"), "\U0001F4F1")
        tr(c4, "Printers", lambda: self.open_shell_command("start ms-settings:printers"), "\U0001F5A8")
        tr(c4, "Bluetooth", lambda: self.open_shell_command("start ms-settings:bluetooth"), "\U0001F4F6")
        tr(c4, "Notifications", lambda: self.open_shell_command("start ms-settings:notifications"), "\U0001F514")
        tr(c4, "Troubleshoot", lambda: self.open_shell_command("start ms-settings:troubleshoot"), "\U0001F6E0")
        tr(c4, "About PC", lambda: self.open_shell_command("start ms-settings:about"), "\u2139")
        ctk.CTkFrame(c4, height=6, fg_color="transparent").pack()

    def _build_tools_advanced_tab(self, tab):
        scroll_frame = self._create_tools_tab_scroller(tab)
        tr = self._tool_row

        # --- Common Tools ---
        c1 = self.create_card(scroll_frame)
        c1.grid(row=0, column=0, padx=(0, 6), pady=6, sticky="nsew")
        self._build_card_header(c1, "Common Tools", "Frequently used utilities", COLORS["accent"])
        tr(c1, "Task Manager", lambda: self.open_sys_tool("taskmgr"), "\U0001F4CA")
        tr(c1, "Control Panel", lambda: self.open_sys_tool("control"), "\u2699")
        tr(c1, "Registry Editor", lambda: self.open_sys_tool("regedit"), "\U0001F4DD")
        tr(c1, "System Information", lambda: self.open_sys_tool("msinfo32"), "\U0001F4BB")
        ctk.CTkFrame(c1, height=6, fg_color="transparent").pack()

        # --- Admin & Management ---
        c2 = self.create_card(scroll_frame)
        c2.grid(row=0, column=1, padx=(6, 0), pady=6, sticky="nsew")
        self._build_card_header(c2, "Admin & Management", "Elevated privilege consoles", COLORS["danger"])
        tr(c2, "Group Policy Editor", lambda: self.open_sys_tool("gpedit.msc"), "\U0001F6E1")
        tr(c2, "Services", lambda: self.open_sys_tool("services.msc"), "\u2699")
        tr(c2, "Device Manager", lambda: self.open_sys_tool("devmgmt.msc"), "\U0001F50C")
        tr(c2, "Event Viewer", lambda: self.open_sys_tool("eventvwr.msc"), "\U0001F4C3")
        ctk.CTkFrame(c2, height=6, fg_color="transparent").pack()

        # --- System Properties ---
        c3 = self.create_card(scroll_frame)
        c3.grid(row=1, column=0, padx=(0, 6), pady=6, sticky="nsew")
        self._build_card_header(c3, "System Properties", "Configuration panels", COLORS["success"])
        tr(c3, "Network Connections", lambda: self.open_sys_tool("ncpa.cpl"), "\U0001F310")
        tr(c3, "Programs & Features", lambda: self.open_sys_tool("appwiz.cpl"), "\U0001F4E6")
        tr(c3, "System Properties", lambda: self.open_sys_tool("sysdm.cpl"), "\U0001F4BB")
        tr(c3, "Power Options", lambda: self.open_sys_tool("powercfg.cpl"), "\u26A1")
        tr(c3, "Date and Time", lambda: self.open_sys_tool("timedate.cpl"), "\U0001F552")
        tr(c3, "Mouse Properties", lambda: self.open_sys_tool("main.cpl"), "\U0001F5B1")
        tr(c3, "Run Dialog", lambda: self.open_shell_command("explorer shell:::{2559a1f3-21d7-11d4-bdaf-00c04f60b9f0}"), "\u25B6")
        ctk.CTkFrame(c3, height=6, fg_color="transparent").pack()

        # --- Monitors & Security ---
        c4 = self.create_card(scroll_frame)
        c4.grid(row=1, column=1, padx=(6, 0), pady=6, sticky="nsew")
        self._build_card_header(c4, "Monitors & Security", "Performance and diagnostics", COLORS["warning"])
        tr(c4, "Resource Monitor", lambda: self.open_sys_tool("resmon"), "\U0001F4CA")
        tr(c4, "Performance Monitor", lambda: self.open_sys_tool("perfmon"), "\U0001F4C8")
        tr(c4, "Computer Management", lambda: self.open_sys_tool("compmgmt.msc"), "\U0001F5A5")
        tr(c4, "Certificate Manager", lambda: self.open_sys_tool("certmgr.msc"), "\U0001F510")
        tr(c4, "Print Management", lambda: self.open_sys_tool("printmanagement.msc"), "\U0001F5A8")
        tr(c4, "Disk Cleanup", lambda: self.open_sys_tool("cleanmgr.exe"), "\U0001F9F9")
        tr(c4, "Disk Management", lambda: self.open_sys_tool("diskmgmt.msc"), "\U0001F4BD")
        tr(c4, "Memory Diagnostic", lambda: self.open_sys_tool("mdsched.exe"), "\U0001F9E0")
        tr(c4, "ODBC Data Sources", lambda: self.open_sys_tool("odbcad32.exe"), "\U0001F4C0")
        tr(c4, "BitLocker Keys", self.get_bitlocker_keys, "\U0001F511", admin=True)
        ctk.CTkFrame(c4, height=6, fg_color="transparent").pack()

        # --- Advanced Network ---
        c5 = self.create_card(scroll_frame)
        c5.grid(row=2, column=0, padx=(0, 6), pady=6, sticky="nsew")
        self._build_card_header(c5, "Advanced Network", "IP, WiFi, and DNS config", COLORS["accent"])
        tr(c5, "Show External IP", self.show_external_ip, "\U0001F30D")
        tr(c5, "Reveal WiFi Passwords", self.reveal_wifi_passwords, "\U0001F4F6", admin=True)
        tr(c5, "Restart WLAN Service", self.restart_wlan_service, "\U0001F4E1", admin=True)
        tr(c5, "DNS: Google (8.8.8.8)", lambda: self.set_dns("8.8.8.8"), "\U0001F310", admin=True)
        tr(c5, "DNS: Cloudflare (1.1.1.1)", lambda: self.set_dns("1.1.1.1"), "\U0001F310", admin=True)
        tr(c5, "DNS: Automatic (DHCP)", self.set_dns_automatic, "\U0001F310", admin=True)
        tr(c5, "Network Reset (Full)", self.network_reset_full, "\U0001F504", admin=True)
        tr(c5, "Network Troubleshooter", self.run_network_troubleshooter, "\U0001F6E0")
        ctk.CTkFrame(c5, height=6, fg_color="transparent").pack()

        # --- File Utilities ---
        c6 = self.create_card(scroll_frame)
        c6.grid(row=2, column=1, padx=(6, 0), pady=6, sticky="nsew")
        self._build_card_header(c6, "File Utilities", "Verify file integrity", COLORS["success"])
        tr(c6, "File Hash (SHA256)", self.calc_file_hash, "\U0001F50D")
        ctk.CTkFrame(c6, height=6, fg_color="transparent").pack()

    def build_file_scanner_frame(self):
        frame = self.content_frames["Scan"]
        for w in frame.winfo_children():
            w.destroy()
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # --- HEADER ---
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 8))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Storage Scanner", font=("Segoe UI Variable Display", 24, "bold"), text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="Find large files and folders taking up space.", font=("Segoe UI", 11),
                     text_color=COLORS["subtext"]).grid(row=1, column=0, sticky="w", pady=(2, 0))
        ctk.CTkFrame(frame, fg_color=COLORS["border"], height=1).grid(row=0, column=0, sticky="ew", pady=(48, 0))

        # --- SCAN CARD ---
        control_frame = ctk.CTkFrame(frame, fg_color=COLORS["card"], corner_radius=16, border_width=1, border_color=COLORS["border"])
        control_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 16))
        control_frame.grid_columnconfigure(1, weight=1)

        card_header = ctk.CTkFrame(control_frame, fg_color="transparent")
        card_header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=16, pady=(16, 4))
        card_header.grid_columnconfigure(1, weight=1)
        ctk.CTkFrame(card_header, width=3, height=18, fg_color=COLORS["accent"], corner_radius=2).grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="ns")
        ctk.CTkLabel(card_header, text="Scan for large files", font=("Segoe UI", 13, "bold"), text_color=COLORS["text"]).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(card_header, text="Choose a drive and run a scan.", font=("Segoe UI", 10),
                     text_color=COLORS["subtext"]).grid(row=1, column=1, sticky="w", pady=(1, 0))
        ctk.CTkFrame(control_frame, fg_color=COLORS["border"], height=1).grid(row=0, column=0, columnspan=3, sticky="ew", padx=16, pady=(56, 0))

        # Row: Drive label, dropdown, Scan button, status
        controls_row = ctk.CTkFrame(control_frame, fg_color="transparent")
        controls_row.grid(row=1, column=0, columnspan=3, sticky="ew", padx=24, pady=(4, 20))
        controls_row.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(controls_row, text="Drive", font=("Segoe UI", 12), text_color=COLORS["subtext"]).grid(row=0, column=0, padx=(0, 10), pady=8, sticky="w")
        try:
            drives = [p.device for p in psutil.disk_partitions() if 'rw' in p.opts]
            if not drives:
                drives = ["C:\\"]
        except Exception:
            drives = ["C:\\"]
        self.drive_menu = ctk.CTkOptionMenu(controls_row, values=drives, width=120, height=40, corner_radius=12,
                                            fg_color=COLORS["bg"], button_color=COLORS["border"], button_hover_color=COLORS["glass_edge"],
                                            font=("Segoe UI", 13))
        self.drive_menu.grid(row=0, column=1, padx=(0, 16), pady=8, sticky="w")

        self.scan_button = ctk.CTkButton(controls_row, text="Scan", height=40, corner_radius=12, font=("Segoe UI", 14, "bold"),
                                         fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color="white",
                                         width=100, command=self._start_large_file_scan_ui)
        self.scan_button.grid(row=0, column=2, padx=(0, 16), pady=8, sticky="w")

        self.scan_status_label = ctk.CTkLabel(controls_row, text="Ready to scan.", font=("Segoe UI", 12),
                                              text_color=COLORS["subtext"], wraplength=320)
        self.scan_status_label.grid(row=0, column=3, padx=0, pady=8, sticky="w")

        self.scan_progress_bar = ctk.CTkProgressBar(control_frame, height=6, corner_radius=3, progress_color=COLORS["accent"],
                                                   fg_color=COLORS["border"])
        self.scan_progress_bar.grid(row=2, column=0, columnspan=3, sticky="ew", padx=24, pady=(0, 20))
        self.scan_progress_bar.grid_remove()

        # --- RESULTS (Apple-style list container) ---
        results_wrapper = ctk.CTkFrame(frame, fg_color="transparent")
        results_wrapper.grid(row=2, column=0, sticky="nsew", padx=4, pady=(0, 4))
        results_wrapper.grid_rowconfigure(1, weight=1)
        results_wrapper.grid_columnconfigure(0, weight=1)

        results_label_row = ctk.CTkFrame(results_wrapper, fg_color="transparent")
        results_label_row.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        results_label_row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(results_label_row, text="Results", font=("Segoe UI", 15, "bold"), text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")

        tree_card = ctk.CTkFrame(results_wrapper, fg_color=COLORS["card"], corner_radius=16, border_width=1, border_color=COLORS["border"])
        tree_card.grid(row=1, column=0, sticky="nsew")
        tree_card.grid_rowconfigure(1, weight=1)
        tree_card.grid_columnconfigure(0, weight=1)

        # Column header bar (subtle, like Finder)
        col_header = ctk.CTkFrame(tree_card, fg_color=COLORS["bg"], height=36, corner_radius=12)
        col_header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 0))
        col_header.grid_propagate(False)
        col_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(col_header, text="Name", font=("Segoe UI", 12, "bold"), text_color=COLORS["subtext"]).grid(row=0, column=0, sticky="w", padx=(16, 0), pady=8)
        ctk.CTkLabel(col_header, text="Size", font=("Segoe UI", 12, "bold"), text_color=COLORS["subtext"]).grid(row=0, column=1, sticky="e", padx=(0, 32), pady=8)

        tree_inner = ctk.CTkFrame(tree_card, fg_color="transparent")
        tree_inner.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        tree_inner.grid_rowconfigure(0, weight=1)
        tree_inner.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=COLORS["card"], foreground=COLORS["text"],
                        fieldbackground=COLORS["card"], borderwidth=0, rowheight=36, font=("Segoe UI", 13))
        style.map("Treeview", background=[("selected", COLORS["accent"])])
        style.configure("Treeview.Heading", background=COLORS["card"], foreground=COLORS["subtext"],
                        font=("Segoe UI", 11, "bold"), borderwidth=0, relief="flat")
        style.map("Treeview.Heading", background=[("active", COLORS["hover"])])
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        self.tree = ttk.Treeview(tree_inner, columns=("size", "path"), show="tree headings")
        self.tree.heading("#0", text="")
        self.tree.heading("size", text="")
        self.tree.heading("path", text="")
        self.tree.column("#0", anchor="w", stretch=True)
        self.tree.column("size", anchor="e", width=100)
        self.tree.column("path", width=0, stretch=False)
        self.tree.grid(row=0, column=0, sticky="nsew")

        vsb = ctk.CTkScrollbar(tree_inner, command=self.tree.yview, fg_color=COLORS["card"],
                               button_color=COLORS["border"], button_hover_color=COLORS["glass_edge"])
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ctk.CTkScrollbar(tree_inner, orientation="horizontal", command=self.tree.xview,
                               fg_color=COLORS["card"], button_color=COLORS["border"], button_hover_color=COLORS["glass_edge"])
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.tag_configure("critical", foreground="#ff5252")
        self.tree.tag_configure("high", foreground="#ff9f43")
        self.tree.tag_configure("medium", foreground="#feca57")

        self.tree.bind("<Button-3>", self._show_tree_context_menu)
        self.tree_context_menu = tk.Menu(self, tearoff=0, bg=COLORS["card"], fg=COLORS["text"],
                                        activebackground=COLORS["accent"], activeforeground=COLORS["text"],
                                        relief="flat", borderwidth=1)
        self.tree_context_menu.add_command(label="Open Location", command=self._tree_open_location)
        self.tree_context_menu.add_command(label="Delete (to Recycle Bin)", command=self._tree_delete_item)

        # Empty state hint (shows when no items)
        self.scanner_empty_label = ctk.CTkLabel(tree_card, text="Select a drive and tap Scan to see large files and folders.",
                                                font=("Segoe UI", 13), text_color=COLORS["subtext"])
        self.scanner_empty_label.place(relx=0.5, rely=0.5, anchor="center")

    def _start_large_file_scan_ui(self):
        if not self.prompt_for_admin("Disk Scan"):
            return

        # Get selected drive
        drive_to_scan = self.drive_menu.get()

        # Clear tree and init streaming state (path -> tree id; pending children when parent not yet inserted)
        for i in self.tree.get_children():
            self.tree.delete(i)
        self._scan_path_to_id = {drive_to_scan: ""}
        self._scan_pending = {}
        self._scan_item_sizes = {}  # node_id -> size for color tags when scan finishes

        self.scan_button.configure(state="disabled", text="Scanning...")
        self.scan_status_label.configure(text=f"Scanning {drive_to_scan}")
        self.scan_progress_bar.set(0)
        self.scan_progress_bar.grid(row=2, column=0, columnspan=3, sticky="ew", padx=24, pady=(0, 20))
        if hasattr(self, "scanner_empty_label"):
            self.scanner_empty_label.place_forget()

        self.log_message(f"Starting disk space scan for {drive_to_scan}")
        
        thread = threading.Thread(target=self._scan_directory_worker, args=(drive_to_scan,), daemon=True)
        thread.start()

    def _build_log_section(self, parent):
        """Build the log viewer inside the Logs page."""
        log_card = self.create_card(parent)
        log_card.pack(fill="both", expand=True, padx=0, pady=0)
        self.log_area = ctk.CTkTextbox(log_card, fg_color=COLORS["bg"], font=("Cascadia Code", 11),
                                       border_width=0, corner_radius=10)
        self.log_area.pack(pady=8, padx=8, fill="both", expand=True)
        self._log_configure_tags_once()

    def _log_configure_tags_once(self):
        """Configure log text tags once so _safe_log does not reconfigure on every message."""
        if getattr(self, "_log_tags_done", False):
            return
        if not getattr(self, "log_area", None) or not self.log_area.winfo_exists():
            return
        try:
            self.log_area.tag_config("INFO", foreground=COLORS["subtext"])
            self.log_area.tag_config("WARN", foreground=COLORS["warning"])
            self.log_area.tag_config("ERROR", foreground=COLORS["danger"])
            self.log_area.tag_config("SUCCESS", foreground=COLORS["success"])
            self.log_area.tag_config("TIME", foreground="#52525b")
            self._log_tags_done = True
        except (tk.TclError, AttributeError):
            pass

    def build_settings_frame(self):
        frame = self.content_frames["Settings"]
        for w in frame.winfo_children():
            w.destroy()
        self.build_header(frame, "Settings", "Customize file sorting rules and appearance")

        scroll_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent",
                                              scrollbar_fg_color=COLORS["bg"],
                                              scrollbar_button_color=COLORS["border"], scrollbar_button_hover_color=COLORS["glass_edge"])
        self._style_scrollable(scroll_frame)
        scroll_frame.pack(fill="both", expand=True, padx=20)

        # --- Sorting Rules card ---
        rules_card = self.create_card(scroll_frame)
        rules_card.pack(fill="x", pady=(0, 12))
        self._build_card_header(rules_card, "Sorting Rules", "Define file extensions per category", COLORS["accent"])
        self.settings_entries = {}
        for category, extensions in self.rules.items():
            row = ctk.CTkFrame(rules_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=3)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row, text=category, font=("Segoe UI", 12, "bold"), width=110, anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=6)
            ext_string = ", ".join(extensions)
            entry = ctk.CTkEntry(row, font=("Consolas", 11), border_color=COLORS["border"],
                                 fg_color=COLORS["bg"], height=32, corner_radius=8)
            entry.insert(0, ext_string)
            entry.grid(row=0, column=1, sticky="ew", pady=6)
            self.settings_entries[category] = entry
        ctk.CTkFrame(rules_card, height=8, fg_color="transparent").pack()

        # --- Appearance card ---
        appearance_card = self.create_card(scroll_frame)
        appearance_card.pack(fill="x", pady=(0, 12))
        self._build_card_header(appearance_card, "Appearance", "Toggle between dark and light mode", COLORS["warning"])
        self._tool_row(appearance_card, "Toggle Dark / Light Mode", self.toggle_theme, "\U0001F3A8")
        ctk.CTkFrame(appearance_card, height=6, fg_color="transparent").pack()

        save_button = self.create_button(frame, "Save All Settings", "primary", self.save_all_settings)
        save_button.pack(pady=20, padx=20, fill="x")

    def build_logs_frame(self):
        frame = self.content_frames["Logs"]
        for w in frame.winfo_children():
            w.destroy()
        self.build_header(frame, "Activity Log", "Timestamped record of actions this session")
        self._build_log_section(frame)

    def save_all_settings(self):
        try:
            for category, entry in self.settings_entries.items():
                ext_text = entry.get()
                # Sanitize: remove spaces, split by comma, filter empty strings, ensure dot prefix
                new_exts = [f".{ext.strip().lstrip('.')}" for ext in ext_text.split(',') if ext.strip()]
                self.rules[category] = sorted(list(set(new_exts))) # Sort and remove duplicates
            
            self.save_config()
            self.log_message("Settings saved successfully.")
            self.show_notification("Settings Saved!", type="success")
        except Exception as e:
            self.log_message(f"Error saving settings: {e}", "ERROR")
            self.show_notification("Error saving settings", type="error")

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)

    def create_card(self, parent, corner_radius=16):
        frame = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=corner_radius, border_width=1, border_color=COLORS["border"])
        return frame

    def create_button(self, parent, text, style, cmd):
        return ctk.CTkButton(parent, text=text, command=cmd,
                             corner_radius=10, height=36, font=("Segoe UI", 12, "bold"),
                             **self.button_styles.get(style, self.button_styles["secondary"]))

    def _build_card_header(self, card, title, subtitle="", accent_color=None):
        """Builds a card header with accent line, title, and optional subtitle."""
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(14, 0))
        ac = accent_color or COLORS["accent"]
        ctk.CTkFrame(hdr, width=3, height=18, fg_color=ac, corner_radius=2).pack(side="left", padx=(0, 10))
        txt_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        txt_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(txt_frame, text=title, font=("Segoe UI", 13, "bold"), text_color=COLORS["text"]).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(txt_frame, text=subtitle, font=("Segoe UI", 10), text_color=COLORS["subtext"]).pack(anchor="w", pady=(1, 0))
        ctk.CTkFrame(card, fg_color=COLORS["border"], height=1).pack(fill="x", padx=16, pady=(10, 4))

    def _tool_row(self, parent, text, cmd, icon=None, warn=False, admin=False):
        """Compact clickable row for tool lists. Returns the row frame for further config."""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent", height=32)
        row_frame.pack(fill="x", padx=10, pady=1)
        row_frame.pack_propagate(False)
        display = f"  {icon}   {text}" if icon else f"  {text}"
        tc = COLORS["text"]
        btn = ctk.CTkButton(row_frame, text=display, command=cmd, anchor="w",
                            height=32, corner_radius=8, fg_color="transparent",
                            hover_color=COLORS["hover"], text_color=tc,
                            font=("Segoe UI", 12), border_width=0)
        btn.pack(side="left", fill="x", expand=True)
        if admin:
            badge = ctk.CTkLabel(row_frame, text="\U0001F6E1 Admin", font=("Segoe UI", 9),
                                 text_color=COLORS["warning"], width=60)
            badge.pack(side="right", padx=(0, 8))
        return btn

    def on_closing(self):
        """Handles window close event to safely stop the observer."""
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        self.destroy()

    def _on_window_resize(self, event):
        # Resize feels laggy because Windows does *live* resize: every small drag sends many Configure
        # events and tkinter re-layouts the whole window each time. No animation = we’d only redraw
        # once on release (snappy but content would jump). We debounce our work so we do less per event.
        if event.widget != self:
            return
        if self._resize_after_id:
            self.after_cancel(self._resize_after_id)
        self._resize_after_id = self.after(100, self._on_resize_debounced)

    def _on_resize_debounced(self):
        self._resize_after_id = None
        if self.active_toasts:
            self._reposition_notifications()
    def _gather_system_info_impl(self):
        """Actual system info gathering (can run in thread). Returns dict."""
        try:
            uname = platform.uname()
            os_info = f"{uname.system} {uname.release}"
            os_info_full = f"{uname.system} {uname.release} ({uname.version})"
            node_name = uname.node
        except Exception:
            os_info = os_info_full = "Unknown"
            node_name = "Unknown"
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            cpu_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            winreg.CloseKey(key)
            cpu_name = cpu_name.strip()
        except Exception:
            cpu_name = platform.processor() or "Unknown"
        ram_gb = f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB"
        return {
            "hostname": node_name, "os": os_info, "os_full": os_info_full,
            "cpu": cpu_name, "ram": ram_gb, "python_version": sys.version.split()[0]
        }

    def get_system_info(self):
        """Returns cached system info, or gathers and caches it (main thread). For background load use _gather_system_info_impl in a thread then set _system_info_cache."""
        if self._system_info_cache is not None:
            return self._system_info_cache
        self._system_info_cache = self._gather_system_info_impl()
        return self._system_info_cache

    def _style_scrollable(self, scroll_frame):
        """Best-effort: restyle CTkScrollableFrame scrollbar and auto-hide when content fits."""
        try:
            sb = scroll_frame._scrollbar
        except AttributeError:
            return
        try:
            sb.configure(width=8)
        except Exception:
            pass

        def _update(_event=None):
            try:
                content_h = scroll_frame._scrollable_frame.winfo_reqheight()
                frame_h = scroll_frame._scrollable_frame.winfo_height() or scroll_frame.winfo_height()
                if content_h <= frame_h + 1:
                    sb.grid_remove()
                else:
                    sb.grid()
            except Exception:
                pass

        def _update_throttled(_event=None):
            aid = getattr(scroll_frame, "_scroll_update_after_id", None)
            if aid:
                try:
                    self.after_cancel(aid)
                except Exception:
                    pass
            scroll_frame._scroll_update_after_id = self.after(120, _update)

        try:
            scroll_frame._scrollable_frame.bind("<Configure>", _update_throttled)
            scroll_frame.bind("<Configure>", _update_throttled)
            self.after(100, _update)
        except Exception:
            pass

    def _reposition_notifications(self):
        """Recalculates and sets the y-position for all active toasts, stacking bottom-up."""
        center_x = (self.winfo_width() - NOTIFICATION_WIDTH) // 2
        current_y_offset = NOTIFICATION_MARGIN_Y
        for toast_info in reversed(self.active_toasts):
            target_y = self.winfo_height() - current_y_offset - toast_info["height"]
            toast_info["target_y"] = target_y
            toast_info["target_x"] = center_x
            if toast_info.get("placed"):
                toast_info["widget"].place(x=center_x, y=target_y)
            current_y_offset += toast_info["height"] + NOTIFICATION_SPACING

    def _animate_toast_in(self, toast_info):
        """Slide the toast up from below the window edge."""
        start_y = self.winfo_height() + 10
        target_y = toast_info["target_y"]
        x = toast_info["target_x"]
        toast_info["placed"] = True
        steps = 8
        dy = (start_y - target_y) / steps

        def _step(i, cy):
            try:
                if not toast_info["widget"].winfo_exists():
                    return
            except tk.TclError:
                return
            if i >= steps:
                toast_info["widget"].place(x=x, y=target_y)
                return
            toast_info["widget"].place(x=x, y=int(cy))
            self.after(16, _step, i + 1, cy - dy)

        _step(0, start_y)

    def _animate_toast_out(self, toast_info):
        """Slide the toast down, then destroy it."""
        if toast_info["id"] not in {t["id"] for t in self.active_toasts}:
            return
        target_y = self.winfo_height() + 10
        try:
            current_y = toast_info["widget"].winfo_y()
        except (tk.TclError, Exception):
            self.active_toasts = [t for t in self.active_toasts if t["id"] != toast_info["id"]]
            return
        steps = 6
        dy = (target_y - current_y) / steps

        def _step(i, cy):
            try:
                if not toast_info["widget"].winfo_exists():
                    self.active_toasts = [t for t in self.active_toasts if t["id"] != toast_info["id"]]
                    return
            except tk.TclError:
                self.active_toasts = [t for t in self.active_toasts if t["id"] != toast_info["id"]]
                return
            if i >= steps:
                self.active_toasts = [t for t in self.active_toasts if t["id"] != toast_info["id"]]
                try:
                    toast_info["widget"].destroy()
                except (tk.TclError, Exception):
                    pass
                self.after(0, self._reposition_notifications)
                return
            try:
                toast_info["widget"].place(x=toast_info["target_x"], y=int(cy))
            except (tk.TclError, Exception):
                pass
            self.after(16, _step, i + 1, cy + dy)

        _step(0, current_y)

    def show_notification(self, message, type="info", duration=None):
        """Display a bottom-center toast notification with slide animation."""
        accent = NOTIFICATION_ACCENT_COLORS.get(type, NOTIFICATION_ACCENT_COLORS["info"])
        icon_char = NOTIFICATION_ICONS.get(type, NOTIFICATION_ICONS["info"])
        if duration is None:
            duration = 5000 if type == "error" else 3000

        # Evict oldest if at max
        while len(self.active_toasts) >= NOTIFICATION_MAX_VISIBLE:
            oldest = self.active_toasts[0]
            self.active_toasts = self.active_toasts[1:]
            try:
                oldest["widget"].destroy()
            except (tk.TclError, Exception):
                pass

        toast_id = self.notification_counter
        self.notification_counter += 1

        toast = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=8,
                             border_width=1, border_color=COLORS["border"],
                             width=NOTIFICATION_WIDTH, height=38)
        toast.pack_propagate(False)
        toast.lift()

        inner = ctk.CTkFrame(toast, fg_color="transparent")
        inner.pack(fill="both", expand=True)

        accent_bar = ctk.CTkFrame(inner, width=3, height=20, fg_color=accent, corner_radius=2)
        accent_bar.pack(side="left", padx=(8, 0))

        icon_label = ctk.CTkLabel(inner, text=icon_char, font=("Segoe UI", 11),
                                  text_color=accent, width=18)
        icon_label.pack(side="left", padx=(6, 4))

        msg_label = ctk.CTkLabel(inner, text=message, font=("Segoe UI", 11),
                                 text_color=COLORS["text"], anchor="w")
        msg_label.pack(side="left", fill="x", expand=True, padx=(0, 10))

        toast_height = 38

        center_x = (self.winfo_width() - NOTIFICATION_WIDTH) // 2

        toast_info = {
            "id": toast_id,
            "widget": toast,
            "target_x": center_x,
            "target_y": self.winfo_height() - NOTIFICATION_MARGIN_Y - toast_height,
            "height": toast_height,
            "placed": False,
        }
        self.active_toasts.append(toast_info)
        self._reposition_notifications()
        self._animate_toast_in(toast_info)

        self.after(duration, lambda tid=toast_id: self._dismiss_toast_by_id(tid))

    def _dismiss_toast_by_id(self, toast_id):
        """Find and animate out a toast by its id."""
        for t in self.active_toasts:
            if t["id"] == toast_id:
                self._animate_toast_out(t)
                return

    def prompt_for_admin(self, feature_name: str) -> bool:
        """Prompts user to restart as admin. Returns True to proceed, False to cancel."""
        if self.is_admin:
            return True

        response = messagebox.askyesnocancel(
            "Administrator rights needed",
            f"'{feature_name}' requires administrator rights.\n\n"
            "• Yes: Launch this app as Administrator (recommended).\n"
            "• No: Try anyway without admin (may fail).\n"
            "• Cancel: Do nothing.",
            icon='warning'
        )

        if response is None:  # Cancel
            return False
        if response is True:  # Yes
            self.show_notification("Launching as Administrator...", duration=1500)
            self.update_idletasks()
            time.sleep(1)
            run_as_admin(getattr(self, "_current_page", "Home"))
            return False
        return True # User chose No, proceed without admin

    def update_vitals(self):
        """Sample CPU/RAM/battery in a background thread so the UI thread never blocks on psutil."""
        def _sample():
            try:
                # interval=0.1 so first call returns a real value (otherwise cpu_percent() returns 0.0 on first call)
                cpu_percent = psutil.cpu_percent(interval=0.1)
                ram_percent = psutil.virtual_memory().percent
                bat = psutil.sensors_battery()
                bat_pct = bat.percent if bat else None
                self.after(0, lambda: self._apply_vitals(cpu_percent, ram_percent, bat_pct))
            except Exception:
                pass
        threading.Thread(target=_sample, daemon=True).start()
        self.after(2000, self.update_vitals)

    def _apply_vitals(self, cpu_percent, ram_percent, bat_pct):
        """Runs on main thread: update labels and graph from sampled values."""
        self.cpu_data.append(cpu_percent)
        self.ram_data.append(ram_percent)
        if getattr(self, "cpu_label", None) and self.cpu_label.winfo_exists():
            self.cpu_label.configure(text=f"CPU  {cpu_percent:.1f}%")
        if getattr(self, "ram_label", None) and self.ram_label.winfo_exists():
            self.ram_label.configure(text=f"RAM  {ram_percent:.1f}%")
        if bat_pct is not None and getattr(self, "bat_label", None) and self.bat_label.winfo_exists():
            self.bat_label.configure(text=f"BAT {bat_pct}%")
        if getattr(self, "cpu_line", None):
            self.update_graph()

    def update_graph(self):
        self.cpu_line.set_ydata(self.cpu_data)
        self.ram_line.set_ydata(self.ram_data)
        self.canvas.draw_idle()

    def setup_observer(self):
        """Initializes the filesystem observer."""
        self.observer = Observer()
        event_handler = GlobalHandler(self)
        self.observer.schedule(event_handler, str(DESKTOP_PATH), recursive=False)

    def toggle_realtime_sort(self):
        """Starts or stops the real-time desktop sorting."""
        self.realtime_active = bool(self.realtime_switch.get())
        if self.realtime_active:
            if not self.observer.is_alive():
                self.setup_observer() # Re-setup if it was stopped
                self.observer.start()
            self.show_notification("Real-time Cleaning Activated", type="success")
        else:
            if self.observer.is_alive():
                self.observer.stop()
                self.observer.join()
            self.show_notification("Real-time Cleaning Deactivated", type="info")

    def toggle_icons(self):
        """Toggles desktop icon visibility without restarting explorer.exe. (Windows Specific)"""
        self.icons_hidden = not self.icons_hidden
        value = 1 if self.icons_hidden else 0

        try:
            # 1. Update Registry using winreg for a pure Python approach
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "HideIcons", 0, winreg.REG_DWORD, value)
            winreg.CloseKey(key)

            # 2. Notify Windows Shell of the change to refresh the desktop without restarting explorer
            ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)

            new_style = "primary" if self.icons_hidden else "tinted"
            self.btn_hide.configure(
                text="Exit Incognito" if self.icons_hidden else "Incognito: Hide Icons",
                **self.button_styles[new_style]
            )
            status = "On" if self.icons_hidden else "Off"
            self.show_notification(f"Incognito Mode {status}", type="info")
        except Exception as e:
            self.show_notification("Error Toggling Icons", type="error")
            print(f"Icon Toggle Error: {e}")

    def purge_clip(self):
        """Clears the system clipboard."""
        pyperclip.copy("")
        self.log_message("Clipboard purged.")
        self.show_notification("Clipboard Purged", type="success")

    def terminate_processes(self, process_names):
        """Terminates a list of processes by name."""
        killed_count = 0
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] in process_names:
                try:
                    proc.kill()
                    self.log_message(f"Terminated process: {proc.info['name']}")
                    killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    self.log_message(f"Could not kill {proc.info['name']}: {e}", "WARN")
        return killed_count

    def clean_m365_credentials(self):
        """Performs a comprehensive Microsoft 365 credential and cache reset."""
        if not messagebox.askokcancel("CRITICAL WARNING",
            "This will close all Office apps and perform a FULL credential reset.\n\n"
            "What will be cleared:\n"
            "• All Microsoft 365 applications will be closed\n"
            "• Identity & authentication caches\n"
            "• Office licensing cache\n"
            "• Teams cache (Classic & New)\n"
            "• Outlook roaming cache\n"
            "• Office Web Extension cache\n"
            "• Credential Manager entries for Office/Teams/OneDrive\n"
            "• Identity registry keys\n\n"
            "You will need to sign in again to ALL Microsoft 365 apps.\n\n"
            "ARE YOU ABSOLUTELY SURE?", icon='warning'):
            return

        if not self.prompt_for_admin("M365 Credential Reset"):
            return

        self.show_notification("Resetting M365 Credentials...", type="info")
        self.update_idletasks()

        # 1. Terminate all M365 processes
        m365_apps = [
            'OUTLOOK.EXE', 'WINWORD.EXE', 'EXCEL.EXE', 'POWERPNT.EXE',
            'MSACCESS.EXE', 'ONENOTE.EXE', 'Teams.exe', 'ms-teams.exe',
            'OneDrive.exe', 'lync.exe', 'MSOUC.EXE', 'olk.exe',
        ]
        killed = self.terminate_processes(m365_apps)
        self.log_message(f"Terminated {killed} M365 process(es).")
        time.sleep(2)

        # 2. Delete credential, identity, and cache folders (comprehensive list)
        paths_to_delete = [
            # Identity & Authentication
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\IdentityCache')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\OneAuth')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Packages\Microsoft.AAD.BrokerPlugin_cw5n1h2txyewy')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\TokenBroker')),
            Path(os.path.expandvars(r'%APPDATA%\Microsoft\TokenBroker')),
            # Office Licensing (16.0 and 15.0)
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Office\16.0\Licensing')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Office\15.0\Licensing')),
            # Office Document / File Cache
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Office\16.0\OfficeFileCache')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Office\15.0\OfficeFileCache')),
            # Teams Classic (entire cache)
            Path(os.path.expandvars(r'%APPDATA%\Microsoft\Teams')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Teams')),
            # Teams (New / Store version)
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Packages\MSTeams_8wekyb3d8bbwe\LocalCache')),
            # Outlook Roaming Cache & Caches
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Outlook\RoamCache')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Outlook\Security')),
            # Office Web Extensions & Wef
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Office\16.0\Wef')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Office\15.0\Wef')),
            # Cloud Experience Host tokens (WAM)
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Packages\Microsoft.Windows.CloudExperienceHost_cw5n1h2txyewy\AC\TokenBroker')),
            # OneDrive cache (user-level; sync will re-establish)
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\OneDrive\logs')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\OneDrive\settings')),
        ]
        paths_to_delete = list(dict.fromkeys(paths_to_delete))
        deleted_count = 0
        for path in paths_to_delete:
            if path.exists():
                try:
                    shutil.rmtree(path, ignore_errors=True)
                    self.log_message(f"Deleted: {path.name}")
                    deleted_count += 1
                except Exception as e:
                    self.log_message(f"Failed to delete {path.name}: {e}", "ERROR")

        # 3. Clear Credential Manager — expanded target matching
        cred_removed = 0
        try:
            result = subprocess.run(["cmdkey", "/list"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            for line in result.stdout.splitlines():
                if "Target:" in line:
                    target = line.split("Target:", 1)[1].strip()
                    target_lower = target.lower()
                    if any(x in target_lower for x in [
                        "microsoftoffice", "teams", "o365", "onedrive",
                        "microsoftaccount", "windowslive", "msteams",
                        "office16", "office15", ".microsoftonline.com",
                        "mso_cachedtoken", "microsoft.aad", "mso_",
                        "outlook", "exchange", "live.com", "login.windows",
                        "office.com", "outlook.office", "onedrive cached",
                        "windowslive.com", "login.microsoftonline",
                        "aad broker", "tokenbroker", "credential_vault",
                    ]):
                        subprocess.run(["cmdkey", "/delete:" + target], creationflags=subprocess.CREATE_NO_WINDOW)
                        self.log_message(f"Removed credential: {target}")
                        cred_removed += 1
        except Exception as e:
            self.log_message(f"Error clearing credentials: {e}", "ERROR")

        # 4. Registry Keys — Identity, Identities, and Licensing (Office 16 & 15)
        reg_keys = [
            r"Software\Microsoft\Office\16.0\Common\Identity",
            r"Software\Microsoft\Office\16.0\Common\Identity\Identities",
            r"Software\Microsoft\Office\15.0\Common\Identity",
            r"Software\Microsoft\Office\15.0\Common\Identity\Identities",
            r"Software\Microsoft\Office\16.0\Common\SignIn",
            r"Software\Microsoft\Office\15.0\Common\SignIn",
        ]
        for key_path in reg_keys:
            try:
                subprocess.run(["reg", "delete", f"HKCU\\{key_path}", "/f"],
                               capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                self.log_message(f"Deleted registry key: {key_path}")
            except Exception as e:
                self.log_message(f"Error deleting registry key {key_path}: {e}", "ERROR")

        self.log_message(f"M365 reset complete — {deleted_count} cache folders cleared, {cred_removed} credentials removed.", "SUCCESS")
        self.show_notification("M365 Reset Complete — Sign in again to continue", type="success")

    def create_restore_point(self):
        if not self.prompt_for_admin("Create Restore Point"):
            return
        if not messagebox.askyesno("Confirm", "This will create a system restore point. This may take a few moments. Continue?"):
            return
        
        self.log_message("Creating system restore point...")
        self.show_notification("Creating Restore Point...", type="info")
        
        # Use PowerShell to create the restore point. This is the most reliable way.
        command = 'powershell.exe -ExecutionPolicy Bypass -NoProfile -Command "Checkpoint-Computer -Description \'Ombra_Utility_Restore_Point\' -RestorePointType \'MODIFY_SETTINGS\'"'
        
        def _worker():
            try:
                # Using CREATE_NO_WINDOW to hide the PowerShell window
                subprocess.run(command, check=True, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                self.after(0, lambda: self.show_notification("Restore Point Created Successfully", type="success"))
                self.log_message("System restore point created.", "SUCCESS")
            except subprocess.CalledProcessError as e:
                error_message = e.stderr.decode('utf-8', errors='ignore').strip()
                if not error_message:
                    error_message = e.stdout.decode('utf-8', errors='ignore').strip()
                # Check for common error: System Restore is turned off.
                if "is turned off" in error_message:
                    self.after(0, lambda: messagebox.showerror("Error", "Could not create restore point.\n\nSystem Restore is disabled on one or more drives. Please enable it in System Properties -> System Protection."))
                    self.log_message("Failed to create restore point: System Restore is disabled.", "ERROR")
                else:
                    self.after(0, lambda: self.show_notification("Failed to Create Restore Point", type="error"))
                    self.log_message(f"Failed to create restore point: {error_message}", "ERROR")
            except Exception as e:
                self.after(0, lambda: self.show_notification("Failed to Create Restore Point", type="error"))
                self.log_message(f"An unexpected error occurred while creating restore point: {e}", "ERROR")

        threading.Thread(target=_worker, daemon=True).start()

    def clear_icon_cache(self):
        if not self.prompt_for_admin("Clear Icon Cache"):
            return
        if not messagebox.askyesno("Confirm", "This will restart Windows Explorer and may cause your desktop to flash. All open Explorer windows will be closed.\n\nContinue?"):
            return
            
        self.log_message("Clearing icon cache...")
        self.show_notification("Clearing Icon Cache...", type="info")

        def _worker():
            try:
                # 1. Kill explorer
                subprocess.run(["taskkill", "/f", "/im", "explorer.exe"], check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                self.log_message("Explorer process terminated.")
                time.sleep(1) # Give it a moment

                # 2. Delete icon cache db
                icon_cache_path = Path(os.path.expandvars(r'%LOCALAPPDATA%\IconCache.db'))
                if icon_cache_path.exists():
                    try:
                        icon_cache_path.unlink()
                        self.log_message("IconCache.db deleted.")
                    except OSError as e:
                        self.log_message(f"Could not delete IconCache.db: {e}", "WARN")
                else:
                    self.log_message("IconCache.db not found (this is normal).")

                # 3. Restart explorer
                subprocess.Popen(["explorer.exe"])
                self.log_message("Explorer process restarted.")
                
                self.after(0, lambda: self.show_notification("Icon Cache Cleared", type="success"))
            except Exception as e:
                self.log_message(f"Failed to clear icon cache: {e}", "ERROR")
                self.after(0, lambda: self.show_notification("Error Clearing Icon Cache", type="error"))
                # Try to restart explorer anyway if it failed
                subprocess.Popen(["explorer.exe"])

        threading.Thread(target=_worker, daemon=True).start()

    def empty_recycle_bin(self):
        if not messagebox.askyesno("Confirm", "This will permanently empty the Recycle Bin. Continue?"):
            return
        try:
            # Flags: No confirmation, no progress UI, no sound
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1 | 2 | 4)
            self.log_message("Recycle Bin emptied.", "SUCCESS")
            self.show_notification("Recycle Bin Emptied", type="success")
        except Exception as e:
            self.log_message(f"Error emptying Recycle Bin: {e}", "ERROR")
            self.show_notification("Error Emptying Recycle Bin", type="error")

    def clean_temp_files(self):
        """Deletes files and folders from the user's temporary directory."""
        if not self.prompt_for_admin("Temp File Cleaning"):
            return

        if not messagebox.askyesno("Confirm Clean", "This will permanently delete files from your temporary folder. Are you sure you want to continue?"):
            return

        temp_dir = Path(os.environ.get("TEMP", ""))
        if not temp_dir.exists():
            self.show_notification("Temp Directory Not Found", type="error")
            return

        self.log_message("Starting temp file cleanup...")
        self.show_notification("Cleaning Temp Files...", type="info")
        self.update_idletasks()

        deleted_count = 0
        error_count = 0
        for item in temp_dir.iterdir():
            try:
                if item.is_file() or item.is_symlink():
                    item.unlink()
                    # self.log_message(f"DEL file: {item.name}") # Too verbose
                    deleted_count += 1
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=False) # Set to False to catch errors
                    # self.log_message(f"DEL dir: {item.name}") # Too verbose
                    deleted_count += 1
            except (PermissionError, OSError) as e:
                self.log_message(f"Could not delete {item.name}: In use.", "WARN")
                error_count += 1
                continue
        
        if deleted_count > 0:
            msg = f"Cleaned {deleted_count} Temp Items"
            if error_count > 0:
                msg += f" ({error_count} in use)"
            self.log_message(msg, "SUCCESS")
            self.show_notification(msg, type="success")
        else:
            self.show_notification("Temp Folder Already Clean", type="info")

    def clear_thumbnail_cache(self):
        """Clear Windows Explorer thumbnail cache (thumbcache_*.db). Frees space; thumbnails will rebuild when you browse."""
        explorer_cache = Path(os.path.expandvars(r"%LocalAppData%\Microsoft\Windows\Explorer"))
        if not explorer_cache.exists():
            self.show_notification("Thumbnail cache path not found", type="info")
            return
        self.log_message("Clearing thumbnail cache...")
        self.show_notification("Clearing Thumbnail Cache...", type="info")
        deleted = 0
        try:
            for f in explorer_cache.glob("thumbcache_*.db"):
                try:
                    f.unlink()
                    deleted += 1
                except (PermissionError, OSError):
                    pass
            for f in explorer_cache.glob("thumbcache_*.db.volatile"):
                try:
                    f.unlink()
                    deleted += 1
                except (PermissionError, OSError):
                    pass
        except Exception as e:
            self.log_message(f"Thumbnail cache clear error: {e}", "ERROR")
            self.show_notification("Error clearing thumbnail cache", type="error")
            return
        if deleted > 0:
            self.log_message(f"Cleared {deleted} thumbnail cache file(s).", "SUCCESS")
            self.show_notification(f"Thumbnail cache cleared ({deleted} file(s))", type="success")
        else:
            self.show_notification("Thumbnail cache already empty or in use", type="info")

    def run_command(self, command, success_msg):
        """Runs a shell command, requires admin, and shows notification."""
        if not self.prompt_for_admin(f"'{' '.join(command)}'"):
            return
        try:
            subprocess.run(command, check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.log_message(f"Ran command: '{' '.join(command)}'", "SUCCESS")
            self.show_notification(success_msg, type="success")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.log_message(f"Command failed: '{' '.join(command)}'. Error: {e}", "ERROR")
            self.show_notification(f"Error: {e}", type="error")

    def flush_dns(self):
        self.run_command(["ipconfig", "/flushdns"], "DNS Cache Flushed Successfully")

    def reset_network_stack(self):
        """Reset TCP/IP stack (netsh int ip reset). Requires reboot to take effect."""
        if not self.prompt_for_admin("Reset Network Stack"):
            return
        self.run_command(["netsh", "int", "ip", "reset"], "Network stack reset. Reboot recommended.")

    def restart_wlan_service(self):
        """Restart WLAN AutoConfig service."""
        if not self.prompt_for_admin("Restart WLAN Service"):
            return
        self.run_command(["net", "stop", "WLAN AutoConfig"], "WLAN service stopped")
        self.after(1500, lambda: self.run_command(["net", "start", "WLAN AutoConfig"], "WLAN service started"))

    def clear_prefetch(self):
        """Clear Windows Prefetch folder (may slightly slow next boot)."""
        if not self.prompt_for_admin("Clear Prefetch"):
            return
        if not messagebox.askyesno("Confirm", "Clear the Prefetch folder? This may slightly slow the next startup."):
            return
        prefetch = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "Prefetch"
        deleted = 0
        try:
            for f in prefetch.glob("*"):
                try:
                    f.unlink()
                    deleted += 1
                except (PermissionError, OSError):
                    pass
            self.log_message(f"Prefetch: removed {deleted} items.", "SUCCESS")
            self.show_notification(f"Prefetch cleared ({deleted} items)", type="success")
        except Exception as e:
            self.log_message(f"Prefetch clear failed: {e}", "ERROR")
            self.show_notification("Prefetch clear failed", type="error")

    def reset_winsock(self):
        self.run_command(["netsh", "winsock", "reset"], "Winsock Reset Successful. Please Reboot.")

    def release_renew_ip(self):
        """Releases and renews the IP address for all adapters."""
        if not self.prompt_for_admin("IP Release/Renew"):
            return
        try:
            self.show_notification("Releasing IP Address...", type="info")
            self.update_idletasks()
            subprocess.run(["ipconfig", "/release"], check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.log_message("IP Address Released.", "SUCCESS")
            
            self.show_notification("Renewing IP Address...", type="info")
            self.update_idletasks()
            time.sleep(1) # Give adapters a moment
            subprocess.run(["ipconfig", "/renew"], check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.log_message("IP Address Renewed.", "SUCCESS")
            self.show_notification("IP Release/Renew Successful", type="success")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.log_message(f"IP command failed: {e}", "ERROR")
            self.show_notification(f"Error: {e}", type="error")

    def run_sfc_scan(self):
        """Runs sfc /scannow in a new administrative command prompt."""
        if not self.prompt_for_admin("System File Checker"):
            return
        
        if not messagebox.askyesno("Confirm SFC Scan", "This will scan and attempt to repair system files. This process can take a long time and cannot be cancelled easily.\n\nAre you sure you want to start?"):
            return

        try:
            self.log_message("Starting SFC /scannow in a new window.")
            self.show_notification("Starting SFC scan...", type="info")
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", "/k sfc /scannow", None, 1)
        except Exception as e:
            self.log_message(f"Failed to start SFC scan: {e}", "ERROR")
            self.show_notification("Failed to start SFC scan", type="error")

    def run_dism_scan(self):
        """Runs DISM restore health."""
        if not self.prompt_for_admin("DISM Repair"): return
        if not messagebox.askyesno("Confirm DISM", "This will run 'DISM /Online /Cleanup-Image /RestoreHealth'.\nIt may take 10-20 minutes. Continue?"): return
        
        self.log_message("Starting DISM repair...")
        self.show_notification("Starting DISM Repair...", type="info")
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", "/k dism /online /cleanup-image /restorehealth", None, 1)
        except Exception as e:
            self.show_notification("Failed to start DISM", type="error")

    def clear_update_cache(self):
        """Clears Windows Update cache."""
        if not self.prompt_for_admin("Clear Update Cache"): return
        if not messagebox.askyesno("Confirm", "This will stop update services and clear the SoftwareDistribution folder. Continue?"): return

        self.show_notification("Clearing Update Cache...", type="info")
        def _worker():
            try:
                subprocess.run("net stop wuauserv", shell=True)
                subprocess.run("net stop bits", shell=True)
                shutil.rmtree(r"C:\Windows\SoftwareDistribution", ignore_errors=True)
                subprocess.run("net start wuauserv", shell=True)
                subprocess.run("net start bits", shell=True)
                self.after(0, lambda: self.show_notification("Update Cache Cleared", type="success"))
                self.log_message("Windows Update cache cleared.", "SUCCESS")
            except Exception as e:
                self.log_message(f"Failed to clear update cache: {e}", "ERROR")
        threading.Thread(target=_worker, daemon=True).start()

    def restart_spooler(self):
        self.run_command(["net", "stop", "spooler"], "Print Spooler Service Stopped")
        self.after(1000, lambda: self.run_command(["net", "start", "spooler"], "Print Spooler Service Started"))

    def restart_explorer(self):
        self.run_command(["taskkill", "/f", "/im", "explorer.exe"], "Explorer Killed")
        self.after(1000, lambda: subprocess.Popen(["explorer.exe"]))

    def generate_battery_report(self):
        path = DESKTOP_PATH / "battery-report.html"
        self.run_command(["powercfg", "/batteryreport", "/output", str(path)], "Battery Report Generated on Desktop")
        self.after(2000, lambda: webbrowser.open(str(path)))

    def get_bitlocker_keys(self):
        if not self.prompt_for_admin("BitLocker Keys"): return
        def _worker():
            try:
                res = subprocess.check_output("manage-bde -protectors -get c:", shell=True).decode()
                self.after(0, lambda: self.log_area.insert("1.0", f"\n{res}\n"))
                self.after(0, lambda: messagebox.showinfo("BitLocker Keys", "Keys have been printed to the Logs tab."))
            except Exception as e:
                self.after(0, lambda: self.show_notification("Failed to get BitLocker keys", type="error"))
        threading.Thread(target=_worker, daemon=True).start()

    def schedule_shutdown(self, seconds):
        self.run_command(["shutdown", "/s", "/t", str(seconds)], f"Shutdown scheduled in {seconds//60} mins")

    def turn_off_monitor(self):
        # Send message to turn off monitor
        SC_MONITORPOWER = 0xF170
        win32_sys_command = 0x0112
        MONITOR_OFF = 2
        ctypes.windll.user32.SendMessageW(ctypes.windll.user32.GetForegroundWindow(), win32_sys_command, SC_MONITORPOWER, MONITOR_OFF)

    def show_external_ip(self):
        def _fetch():
            try:
                ip = urllib.request.urlopen('https://api.ipify.org', timeout=3).read().decode('utf8')
                self.after(0, lambda: messagebox.showinfo("External IP", f"Your Public IP is:\n{ip}"))
            except Exception as e:
                self.after(0, lambda: self.show_notification("Failed to fetch IP", type="error"))
        threading.Thread(target=_fetch, daemon=True).start()

    def reveal_wifi_passwords(self):
        if not self.prompt_for_admin("WiFi Revealer"): return
        def _scan():
            try:
                data = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles']).decode('utf-8', errors="ignore")
                profiles = [line.split(":")[1][1:-1] for line in data.splitlines() if "All User Profile" in line]
                
                report = "SAVED WIFI PASSWORDS:\n\n"
                for p in profiles:
                    try:
                        res = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', p, 'key=clear']).decode('utf-8', errors="ignore")
                        key_lines = [line.split(":")[1][1:-1] for line in res.splitlines() if "Key Content" in line]
                        key = key_lines[0] if key_lines else "(None)"
                        report += f"SSID: {p}\nPASS: {key}\n{'-'*20}\n"
                    except: pass
                
                self.after(0, lambda: self.log_area.insert("1.0", report))
                self.after(0, lambda: messagebox.showinfo("WiFi Passwords", "Passwords have been printed to the Logs tab."))
            except:
                self.after(0, lambda: self.show_notification("Error retrieving WiFi data", type="error"))
        threading.Thread(target=_scan, daemon=True).start()

    def set_dns(self, dns_ip):
        if not self.prompt_for_admin("DNS Changer"): return
        # Try to set for Wi-Fi and Ethernet
        self.run_command(["netsh", "interface", "ip", "set", "dns", "name=\"Wi-Fi\"", "source=static", f"addr={dns_ip}"], "DNS Set for Wi-Fi")
        self.run_command(["netsh", "interface", "ip", "set", "dns", "name=\"Ethernet\"", "source=static", f"addr={dns_ip}"], "DNS Set for Ethernet")

    def set_dns_automatic(self):
        """Set DNS back to DHCP (obtain automatically)."""
        if not self.prompt_for_admin("DNS Automatic"): return
        self.run_command(["netsh", "interface", "ip", "set", "dns", "name=\"Wi-Fi\"", "source=dhcp"], "DNS set to automatic (Wi-Fi)")
        self.run_command(["netsh", "interface", "ip", "set", "dns", "name=\"Ethernet\"", "source=dhcp"], "DNS set to automatic (Ethernet)")

    def clear_delivery_optimization(self):
        """Clear Delivery Optimization cache (Windows Update peer cache)."""
        if not self.prompt_for_admin("Clear Delivery Optimization"): return
        path = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "SoftwareDistribution" / "DeliveryOptimization"
        if path.exists():
            try:
                shutil.rmtree(path, ignore_errors=True)
                self.log_message("Delivery Optimization cache cleared.", "SUCCESS")
                self.show_notification("Delivery Optimization cache cleared", type="success")
            except Exception as e:
                self.log_message(f"Failed: {e}", "ERROR")
        else:
            self.log_message("Delivery Optimization folder not found (nothing to clear).")

    def clear_windows_error_reports(self):
        """Clear Windows Error Reporting (WER) report queue; frees space."""
        if not self.prompt_for_admin("Clear Error Reports"): return
        if not messagebox.askyesno("Confirm", "Clear Windows Error Reporting local report storage? This does not affect reliability history."): return
        base = Path(os.environ.get("ProgramData", "C:\\ProgramData")) / "Microsoft" / "Windows" / "WER"
        deleted = 0
        for sub in ["ReportQueue", "ReportArchive", "Temp"]:
            p = base / sub
            if p.exists():
                try:
                    for f in p.glob("*"):
                        try: f.unlink(); deleted += 1
                        except (PermissionError, OSError): pass
                    self.log_message(f"Cleared WER {sub}.", "SUCCESS")
                except Exception as e:
                    self.log_message(f"WER {sub}: {e}", "ERROR")
        self.show_notification("Error report cache cleared", type="success" if deleted else "info")

    def clear_browser_cache(self):
        """Clear Edge and Chrome cache folders (close browsers first)."""
        if not messagebox.askyesno("Confirm", "Close Edge and Chrome before continuing. Clear browser cache folders now?"): return
        local = Path(os.path.expandvars(r"%LOCALAPPDATA%"))
        paths = [
            local / "Microsoft" / "Edge" / "User Data" / "Default" / "Cache",
            local / "Microsoft" / "Edge" / "User Data" / "Default" / "Code Cache",
            local / "Google" / "Chrome" / "User Data" / "Default" / "Cache",
            local / "Google" / "Chrome" / "User Data" / "Default" / "Code Cache",
        ]
        for p in paths:
            if p.exists():
                try:
                    shutil.rmtree(p, ignore_errors=True)
                    self.log_message(f"Cleared: {p.name}")
                except Exception as e:
                    self.log_message(f"Failed {p.name}: {e}", "ERROR")
        self.show_notification("Browser cache clear attempted", type="success")

    def network_reset_full(self):
        """Open Network status so user can run full Windows network reset (removes/reinstalls adapters; reboot required)."""
        self.open_shell_command("start ms-settings:network-status")
        self.log_message("Opened Network status. Use 'Network reset' for full reset (reboot required).")
        self.show_notification("Use 'Network reset' on the page for full reset", type="info")

    def run_network_troubleshooter(self):
        self.open_shell_command("start ms-settings:troubleshoot")
        self.log_message("Opened Troubleshoot settings.")

    def sync_time_windows(self):
        """Synchronize Windows time with NTP."""
        if not self.prompt_for_admin("Sync Time"): return
        self.run_command(["w32tm", "/resync"], "Time synchronized")

    def open_task_scheduler(self):
        self.open_sys_tool("taskschd.msc")

    def reliability_monitor(self):
        self.open_shell_command("start perfmon /rel")

    def restart_audio_service(self):
        """Restart Windows Audio service (fixes no sound issues)."""
        if not self.prompt_for_admin("Restart Audio"): return
        self.run_command(["net", "stop", "Audiosrv"], "Audio service stopped")
        self.after(1500, lambda: self.run_command(["net", "start", "Audiosrv"], "Audio service started"))

    def run_disk_cleanup(self):
        """Launch Disk Cleanup (cleanmgr) for C: drive."""
        self.open_sys_tool("cleanmgr /d C:")

    def calc_file_hash(self):
        file_path = ctk.filedialog.askopenfilename()
        if file_path:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            h = sha256_hash.hexdigest()
            self.log_message(f"File: {Path(file_path).name}\nSHA256: {h}")
            messagebox.showinfo("SHA256 Hash", h)
            pyperclip.copy(h)

    def _format_scan_size(self, size_bytes):
        if size_bytes == 0:
            return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024))) if size_bytes > 0 else 0
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"

    def _get_scan_size_tag(self, item_size, root_size):
        if not root_size:
            return ""
        pct = item_size / root_size
        if pct > 0.15: return "critical"
        if pct > 0.05: return "high"
        if pct > 0.01: return "medium"
        return ""

    def _insert_scan_node(self, parent_path, node):
        """Insert one node under parent_path; queue if parent not yet in tree."""
        parent_id = self._scan_path_to_id.get(parent_path)
        if parent_id is None:
            self._scan_pending.setdefault(parent_path, []).append(node)
            return
        icon = "📁" if node["type"] == "folder" else "📄"
        text = f" {icon} {node['name']}"
        size_str = self._format_scan_size(node["size"])
        node_id = self.tree.insert(parent_id, "end", text=text, values=(size_str, node["path"]), open=False)
        self._scan_path_to_id[node["path"]] = node_id
        self._scan_item_sizes[node_id] = node["size"]
        for pending in self._scan_pending.pop(node["path"], []):
            self._insert_scan_node(node["path"], pending)

    def _insert_scan_batch(self, batch):
        """Insert a batch of (parent_path, node) so results appear as we scan."""
        for parent_path, node in batch:
            self._insert_scan_node(parent_path, node)

    def _set_scan_progress(self, fraction, status_text=None):
        """Update the scan progress bar (0.0–1.0) and optionally the status label."""
        try:
            self.scan_progress_bar.set(min(1.0, max(0.0, fraction)))
            if status_text is not None:
                self.scan_status_label.configure(text=status_text)
        except Exception:
            pass

    def _scan_finish(self, root_size=None):
        """Called when worker has finished; apply size-based colors then hide progress."""
        self._set_scan_progress(1.0)
        if root_size and getattr(self, "_scan_item_sizes", None):
            for item_id, size in self._scan_item_sizes.items():
                tag = self._get_scan_size_tag(size, root_size)
                try:
                    self.tree.item(item_id, tags=(tag,) if tag else ())
                except tk.TclError:
                    pass
            self._scan_item_sizes.clear()
        self.on_scan_complete("Scan complete.")

    def _scan_directory_worker(self, root_path):
        """Count dirs first for accurate progress, then single scan with throttled UI updates."""
        batch = []
        BATCH_SIZE = 200
        PROGRESS_EVERY = 50  # Update bar every N dirs so it's smooth but not overwhelming

        def flush_batch():
            if batch:
                self.after(0, self._insert_scan_batch, batch[:])
                batch.clear()

        def count_dirs(path):
            """Minimal walk: only count directories (no stat, no lists)."""
            n = 0
            try:
                with os.scandir(path) as it:
                    for entry in it:
                        if entry.is_dir(follow_symlinks=False):
                            n += 1 + count_dirs(entry.path)
            except (PermissionError, FileNotFoundError):
                pass
            return n

        try:
            self.after(0, lambda: self._set_scan_progress(0, f"Counting folders on {root_path}…"))
            total_dirs = count_dirs(root_path)
            if total_dirs == 0:
                total_dirs = 1
            self.after(0, lambda: self._set_scan_progress(0, f"Scanning {root_path}"))
            dirs_done = [0]

            def _build_tree(path):
                total_size = 0
                children = []
                try:
                    with os.scandir(path) as it:
                        for entry in it:
                            if entry.is_dir(follow_symlinks=False):
                                child_node = _build_tree(entry.path)
                                if child_node["size"] > 0:
                                    children.append(child_node)
                                    total_size += child_node["size"]
                            elif entry.is_file(follow_symlinks=False):
                                try:
                                    st = entry.stat(follow_symlinks=False)
                                    file_size = st.st_size
                                    total_size += file_size
                                    if file_size > 1024 * 1024:
                                        children.append({"name": entry.name, "path": entry.path, "size": file_size, "type": "file"})
                                except (FileNotFoundError, PermissionError):
                                    pass
                except (PermissionError, FileNotFoundError):
                    pass
                dirs_done[0] += 1
                if dirs_done[0] % PROGRESS_EVERY == 0 or dirs_done[0] == total_dirs:
                    pct = dirs_done[0] / total_dirs
                    self.after(0, lambda p=pct: self._set_scan_progress(p))
                children.sort(key=lambda x: x["size"], reverse=True)
                for child in children:
                    batch.append((path, child))
                    if len(batch) >= BATCH_SIZE:
                        flush_batch()
                return {"name": os.path.basename(path) or path, "path": path, "size": total_size, "type": "folder", "children": children}

            tree_data = _build_tree(root_path)
            flush_batch()
            self.after(0, self._scan_finish, tree_data["size"])
        except Exception as e:
            self.log_message(f"Disk scan failed: {e}", "ERROR")
            self.after(0, self.on_scan_complete, "Scan Failed!")

    _TREEVIEW_CHUNK = 130  # Insert this many nodes per idle tick (fewer redraws, faster done)

    def _populate_treeview(self, root_node):
        self.log_message("Scan complete. Populating view...")
        self.scan_status_label.configure(text="Populating view...")
        for i in self.tree.get_children():
            self.tree.delete(i)
        root_size = root_node["size"]
        root_children = sorted(root_node.get("children", []), key=lambda x: x["size"], reverse=True)
        pending = [("", root_children, root_size)]
        self._treeview_pending = pending
        self.after(0, self._insert_treeview_chunk, root_size)

    def _insert_treeview_chunk(self, root_size):
        pending = getattr(self, "_treeview_pending", None)
        if not pending or not getattr(self, "tree", None) or not self.tree.winfo_exists():
            self.on_scan_complete("Scan Complete.")
            return
        chunk = self._TREEVIEW_CHUNK
        processed = 0
        while pending and processed < chunk:
            parent_id, sorted_children, rs = pending.pop(0)
            for i, child in enumerate(sorted_children):
                if processed >= chunk:
                    pending.insert(0, (parent_id, sorted_children[i:], rs))
                    break
                tag = ""
                if rs > 0:
                    pct = child["size"] / rs
                    if pct > 0.15: tag = "critical"
                    elif pct > 0.05: tag = "high"
                    elif pct > 0.01: tag = "medium"
                icon = "📁" if child["type"] == "folder" else "📄"
                size_str = self._format_scan_size(child["size"])
                node_id = self.tree.insert(parent_id, "end", text=f" {icon} {child['name']}",
                                          values=(size_str, child["path"]),
                                          open=(child["size"] > rs * 0.1),
                                          tags=(tag,) if tag else ())
                processed += 1
                if child["type"] == "folder":
                    kids = sorted(child.get("children", []), key=lambda x: x["size"], reverse=True)
                    pending.append((node_id, kids, rs))
        if pending:
            self.after(0, self._insert_treeview_chunk, root_size)
        else:
            self.on_scan_complete("Scan Complete.")
            self._treeview_pending = None

    def _format_scan_size(self, size_bytes):
        if size_bytes == 0:
            return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024))) if size_bytes > 0 else 0
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"

    def on_scan_complete(self, status_text):
        try:
            self.scan_progress_bar.set(1.0)
        except Exception:
            pass
        self.scan_progress_bar.grid_remove()
        self.scan_button.configure(state="normal", text="Scan")
        self.scan_status_label.configure(text=status_text)
        if hasattr(self, "scanner_empty_label") and not self.tree.get_children():
            self.scanner_empty_label.place(relx=0.5, rely=0.5, anchor="center")

    def _show_tree_context_menu(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            self.tree_context_menu.post(event.x_root, event.y_root)

    def _tree_open_location(self):
        if not self.tree.selection():
            return
        selected_id = self.tree.selection()[0]
        path_str = self.tree.item(selected_id, 'values')[1]
        
        try:
            # If it's a file, select it in explorer. If it's a folder, just open it.
            path_obj = Path(path_str)
            if path_obj.is_file():
                subprocess.run(['explorer', '/select,', str(path_obj)])
            else:
                os.startfile(path_str)
            self.log_message(f"Opened location: {path_str}")
        except Exception as e:
            self.log_message(f"Could not open location {path_str}: {e}", "ERROR")
            self.show_notification("Error opening location", type="error")

    def _tree_delete_item(self):
        if not self.tree.selection():
            return
        selected_id = self.tree.selection()[0]
        path_str = self.tree.item(selected_id, 'values')[1]
        
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to move this item to the Recycle Bin?\n\n{path_str}"):
            return

        if send_to_recycle_bin(str(path_str)):
            self.log_message(f"Moved to Recycle Bin: {path_str}", "SUCCESS")
            self.show_notification("Item moved to Recycle Bin", type="success")
            # Remove from treeview
            self.tree.delete(selected_id)
            if hasattr(self, "scanner_empty_label") and not self.tree.get_children():
                self.scanner_empty_label.place(relx=0.5, rely=0.5, anchor="center")
            # Note: Parent sizes will not be updated. A rescan is needed for accuracy.
            self.scan_status_label.configure(text="Item deleted. Sizes may be inaccurate until next scan.")
        else:
            self.log_message(f"Failed to move to Recycle Bin: {path_str}", "ERROR")
            self.show_notification("Failed to delete item", type="error")

    def open_sys_tool(self, tool):
        try:
            subprocess.Popen(tool)
            self.log_message(f"Opened system tool: {tool}")
        except FileNotFoundError:
            self.log_message(f"Could not open {tool}", "ERROR")
            self.show_notification(f"Could not open {tool}", type="error")

    def open_shell_command(self, command):
        """Executes a command using the shell, e.g., for 'start' commands."""
        try:
            subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.log_message(f"Executed shell command: {command}")
        except Exception as e:
            self.log_message(f"Could not execute {command}: {e}", "ERROR")
            self.show_notification(f"Could not execute {command}", type="error")

    def _perform_folder_sort(self, source_path: Path, cleanup_folder_name: str, friendly_name: str):
        """Generic function to sort files from a source path into a cleanup folder."""
        script_name = Path(sys.argv[0]).name
        target_base = source_path / cleanup_folder_name

        files_to_move = []
        for item in source_path.iterdir():
            if item.is_file() and not item.name.startswith('.') and item.name != script_name:
                # Check if it matches any rule before adding
                for category, exts in self.rules.items():
                    if item.suffix.lower() in exts:
                        files_to_move.append(item)
                        break
        
        if not files_to_move:
            self.show_notification(f"{friendly_name} is already clean", type="info")
            return

        if not messagebox.askyesno(f"Confirm {friendly_name} Clean", f"This will move {len(files_to_move)} item(s) into the '{target_base.name}' folder.\n\nAre you sure you want to continue?"):
            self.log_message(f"{friendly_name} clean cancelled by user.")
            return

        sorted_files = []
        error_files = []
        for item in files_to_move:
            for category, exts in self.rules.items():
                if item.suffix.lower() in exts:
                    dest_dir = target_base / category
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    try:
                        # Handle name collision
                        new_dest = dest_dir / item.name
                        if new_dest.exists():
                            base, ext = item.stem, item.suffix
                            i = 1
                            while new_dest.exists():
                                new_dest = dest_dir / f"{base}_{i}{ext}"
                                i += 1
                        
                        shutil.move(str(item), str(new_dest))
                        self.log_message(f"Cleaned '{item.name}' to {category} from {friendly_name}")
                        sorted_files.append(item.name)
                    except (shutil.Error, OSError) as e:
                        self.log_message(f"Could not clean '{item.name}' from {friendly_name}: {e}", "ERROR")
                        error_files.append(item.name)
                    break # Move to next file once categorized

        if sorted_files:
            self.show_notification(f"Cleaned {len(sorted_files)} Items from {friendly_name}", type="success")
        elif not error_files:
            self.show_notification(f"{friendly_name} is already clean", type="info")

    def perform_sort(self):
        """Wrapper to clean the Desktop folder."""
        self._perform_folder_sort(DESKTOP_PATH, "Desktop_Cleanup", "Desktop")

    def perform_downloads_sort(self):
        """Wrapper to clean the Downloads folder."""
        self._perform_folder_sort(DOWNLOADS_PATH, "Downloads_Cleanup", "Downloads Folder")

    def _load_config_async(self):
        """Load config from disk in background; apply on main thread. Does not write config."""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    rules = dict(config.get("sorting_rules", DEFAULT_RULES))
            else:
                self.after(0, lambda: self._apply_config(dict(DEFAULT_RULES)))
                return
        except (json.JSONDecodeError, IOError):
            self.after(0, lambda: self._apply_config(dict(DEFAULT_RULES)))
            return
        self.after(0, self._apply_config, rules)

    def _apply_config(self, rules):
        self.rules = rules

    def load_config(self):
        """Load config from disk; use defaults if missing or invalid. Does not write config on startup."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    self.rules = config.get("sorting_rules", DEFAULT_RULES)
            except (json.JSONDecodeError, IOError):
                self.rules = dict(DEFAULT_RULES)
        else:
            self.rules = dict(DEFAULT_RULES)

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({"sorting_rules": self.rules}, f, indent=4)
        except IOError as e:
            self.show_notification(f"Error saving config: {e}", type="error")

if __name__ == "__main__":
    app = OmbraApp()
    app.mainloop()