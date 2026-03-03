import os
import shutil
from collections import deque
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
import matplotlib
import hashlib
import urllib.request
import zipfile
import io
matplotlib.use("TkAgg") # Set backend for tkinter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- iOS 26 LIQUID GLASS THEME ---
COLORS = {
    "bg": "#000000",           # True Black (iOS 26 Dark)
    "card": "#1c1c1e",         # Elevated Surface
    "card_border": "#2c2c2e",  # Subtle Card Border
    "accent": "#0a84ff",       # System Blue
    "accent_hover": "#409cff", # Blue Hover
    "text": "#ffffff",         # Primary Text
    "subtext": "#8e8e93",      # Secondary Text (iOS Gray)
    "success": "#30d158",      # System Green
    "warning": "#ff9f0a",      # System Orange
    "danger": "#ff453a",       # System Red
    "border": "#2c2c2e",       # Border
    "hover": "#2c2c2e",        # Hover Fill
    "glass_edge": "#48484a"    # Glass Highlight Edge
}

NAV_ICONS = {
    # Use single-codepoint icons to avoid alignment glitches
    "Dashboard": "🏠", "Tools": "🛠", "File Scanner": "📊",
    "Installer": "📦", "Sys Info": "💻", "Logs": "📋", "Settings": "⚙️",
}

# --- SOFTWARE INSTALLER CONFIG ---
SOFTWARE_TO_INSTALL = {
    "Google Chrome": "Google.Chrome",
    "Mozilla Firefox": "Mozilla.Firefox",
    "7-Zip": "7zip.7zip",
    "Notepad++": "Notepad++.Notepad++",
    "VLC Media Player": "VideoLAN.VLC",
    "Adobe Acrobat Reader": "Adobe.Acrobat.Reader.DC",
    "Discord": "Discord.Discord",
    "Steam": "Valve.Steam",
    "Zoom": "Zoom.Zoom",
    "Spotify": "Spotify.Spotify",
    "WhatsApp": "WhatsApp.WhatsApp",
    "Slack": "Slack.Slack",
    "Visual Studio Code": "Microsoft.VisualStudioCode",
    "Python 3.12": "Python.Python.3.12",
    "Node.js LTS": "OpenJS.NodeJS.LTS"
}
# --- CONSTANTS ---
DESKTOP_PATH = Path.home() / "Desktop"
DOWNLOADS_PATH = Path.home() / "Downloads"
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"

# Notification Constants
NOTIFICATION_WIDTH = 350
NOTIFICATION_SPACING = 10
NOTIFICATION_MARGIN_X = 15
NOTIFICATION_MARGIN_Y = 15
CONFIG_FILE = Path("config.json")

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

def run_as_admin():
    """Re-launches the script with administrative privileges."""
    try:
        if getattr(sys, 'frozen', False):
            # If running as compiled EXE
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, None, None, 1)
        else:
            # If running as Python script
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    except Exception as e:
        print(f"Failed to elevate privileges: {e}")

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

def is_winget_available():
    """Checks if the winget command is available on the system."""
    try:
        subprocess.run(["winget", "--version"], capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_installed_software():
    """Uses winget to get a list of installed software and returns a set of IDs."""
    installed_ids = set()
    if not is_winget_available():
        return installed_ids
    try:
        result = subprocess.run(["winget", "list", "--source", "winget"], capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        for line in result.stdout.splitlines():
            parts = line.split()
            if not parts or line.startswith("Name") or line.startswith("---"):
                continue
            installed_ids.add(parts[-1]) # The ID is the last part of the line
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass # Silently fail if winget list fails
    return installed_ids

class GlobalHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app
    def on_modified(self, event):
        if self.app.realtime_active and not event.is_directory:
            self.app.after(0, self.app.debounce_sort)

class OmbraApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # Keep hidden until fully built (splash is shown instead)

        self.realtime_active = False
        self.observer = None
        self.icons_hidden = False
        self.is_admin = is_admin()
        self.rules = {}
        self.load_config()
        self.installed_software_ids = set()
        self.sort_timer = None
        self.ping_thread = None

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
            "danger": {"fg_color": "#1a0a0a", "hover_color": "#3a1515", "border_width": 1, "border_color": COLORS["danger"], "text_color": COLORS["danger"]},
            "tinted": {"fg_color": "#1a3a5c", "hover_color": "#2a4a6c", "text_color": COLORS["accent"], "border_width": 0},
        }

        # --- DYNAMIC WINDOW SIZING ---
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        win_width = 980
        win_height = 720
        if win_height > screen_height - 50: # Ensure it fits with taskbar
            win_height = screen_height - 50

        # --- WINDOW SETUP ---
        admin_title = "  ·  Admin" if self.is_admin else ""
        self.title(f"Ombra Utility Pro{admin_title}")
        self.geometry(f"{win_width}x{win_height}")
        self.configure(fg_color=COLORS["bg"])
        self.minsize(860, 620)

        # --- LAYOUT ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SPLASH OVERLAY (show first, remove after UI is built) ---
        splash_frame = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0, border_width=0)
        splash_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        splash_inner = ctk.CTkFrame(splash_frame, fg_color=COLORS["card"], corner_radius=20, border_width=1, border_color=COLORS["border"], width=380, height=160)
        splash_inner.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(splash_inner, text="OMBRA", font=("Segoe UI Variable Display", 24, "bold"), text_color=COLORS["text"]).pack(pady=(24, 0))
        ctk.CTkLabel(splash_inner, text="Utility Pro", font=("Segoe UI", 11), text_color=COLORS["subtext"]).pack()
        ctk.CTkLabel(splash_inner, text="Loading…", font=("Segoe UI", 11), text_color=COLORS["accent"]).pack(pady=(12, 10))
        splash_progress = ctk.CTkProgressBar(splash_inner, width=280, height=6, progress_color=COLORS["accent"], fg_color=COLORS["border"], mode="indeterminate", indeterminate_speed=1.2)
        splash_progress.pack(pady=(0, 24))
        splash_progress.start()
        self.deiconify()
        self.update_idletasks()
        self.update()  # Show window with only splash first

        # --- SIDEBAR (iOS 26 Glass Panel) ---
        self.nav_frame = ctk.CTkFrame(self, width=270, corner_radius=0, fg_color=COLORS["bg"], border_width=0)
        self.nav_frame.grid(row=0, column=0, sticky="nsew", rowspan=2)
        self.nav_frame.grid_propagate(False)
        splash_frame.lift()
        self.update_idletasks()
        self.update()

        self.sidebar_border = ctk.CTkFrame(self.nav_frame, width=1, fg_color=COLORS["border"])
        self.sidebar_border.pack(side="right", fill="y")

        self.sidebar_content = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
        self.sidebar_content.pack(fill="both", expand=True, padx=20, pady=20)

        # Branding
        brand_frame = ctk.CTkFrame(self.sidebar_content, fg_color="transparent")
        brand_frame.pack(pady=(10, 4), anchor="w")
        ctk.CTkLabel(brand_frame, text="OMBRA", font=("Segoe UI Variable Display", 26, "bold"), text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(brand_frame, text="Utility Pro", font=("Segoe UI", 13), text_color=COLORS["subtext"]).pack(anchor="w")

        # Admin Status Badge
        admin_color = COLORS["success"] if self.is_admin else COLORS["warning"]
        admin_text = "●  Administrator" if self.is_admin else "●  Standard User"
        ctk.CTkLabel(self.sidebar_content, text=admin_text, font=("Segoe UI", 11, "bold"),
                     text_color=admin_color).pack(pady=(4, 20), anchor="w")

        # Navigation Buttons
        self.nav_buttons = {}
        nav_items = ["Dashboard", "Tools", "File Scanner", "Installer", "Sys Info", "Logs", "Settings"]

        for name in nav_items:
            icon = NAV_ICONS.get(name, "")
            display = f"  {icon}   {name}"
            # Keep border_width=1 on all so selected state doesn't shift layout (inactive border = bg color)
            btn = ctk.CTkButton(self.sidebar_content, text=display, image=None, height=44,
                                font=("Segoe UI", 14), corner_radius=14, anchor="w",
                                fg_color="transparent", hover_color=COLORS["hover"], text_color=COLORS["subtext"],
                                border_width=1, border_color=COLORS["bg"], command=lambda n=name: self.show_frame(n))
            btn.pack(pady=3, padx=8, fill="x")
            self.nav_buttons[name] = btn

        # Sidebar Footer
        sidebar_footer = ctk.CTkFrame(self.sidebar_content, fg_color="transparent")
        sidebar_footer.pack(side="bottom", fill="x", pady=(0, 5))
        ctk.CTkLabel(sidebar_footer, text="v2.0", font=("Segoe UI", 11), text_color=COLORS["glass_edge"]).pack(anchor="w")
        if not self.is_admin:
            ctk.CTkButton(sidebar_footer, text="Launch as Administrator", height=36, corner_radius=14,
                          font=("Segoe UI", 12, "bold"), fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                          text_color="white", border_width=0,
                          command=run_as_admin).pack(fill="x", pady=(8, 0))

        # --- CONTENT FRAMES ---
        self.content_frames = {}
        for name in nav_items:
            frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
            frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            self.content_frames[name] = frame
        splash_frame.lift()
        self.update_idletasks()
        self.update()

        # --- BUILD UI FOR EACH FRAME ---
        self.build_dashboard_frame()
        self.build_sysinfo_frame()
        self.build_installer_frame()
        self.build_tools_frame()
        self.build_file_scanner_frame() # New: Build the file scanner frame
        self.build_logs_frame()
        self.build_settings_frame()
        splash_frame.lift()
        self.update_idletasks()
        self.update()

        self.update_vitals()
        self.update_dashboard_extras() # Start extra dashboard loops
        self.setup_observer()
        self.bind("<Configure>", self._on_window_resize) # Bind resize event for notifications
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.show_frame("Dashboard") # Show initial frame

        # Keep splash on top, then hide after delay
        splash_frame.lift()
        self.lift()
        self.update_idletasks()

        def _remove_splash():
            try:
                splash_progress.stop()
            except Exception:
                pass
            try:
                splash_frame.grid_remove()  # Hide without destroying
            except Exception:
                pass
            self.lift()
            self.focus_force()
        self.after(1500, _remove_splash)  # Show splash ~1.5s so user sees it's loading

    def debounce_sort(self):
        if self.sort_timer:
            self.after_cancel(self.sort_timer)
        self.sort_timer = self.after(1500, self.perform_sort)

    def show_frame(self, name):
        """Raises a content frame to the top and updates nav button state."""
        for frame_name, frame in self.content_frames.items():
            if frame_name == name:
                frame.tkraise()
                # Active: same border_width so layout doesn't shift; visible border
                self.nav_buttons[frame_name].configure(fg_color=COLORS["hover"], text_color=COLORS["text"],
                                                       border_width=1, border_color=COLORS["glass_edge"])
            else:
                # Inactive: same border_width, border matches bg so no visual shift
                self.nav_buttons[frame_name].configure(fg_color="transparent", text_color=COLORS["subtext"],
                                                       border_width=1, border_color=COLORS["bg"])

    def log_message(self, message, level="INFO"):
        """Safely logs a message to the UI log area and console."""
        print(f"[{level}] {message}") # Console
        self.after(0, self._safe_log, message, level)

    def _safe_log(self, message, level):
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Configure tags if not already done (idempotent)
        self.log_area.tag_config("INFO", foreground=COLORS["subtext"])
        self.log_area.tag_config("WARN", foreground=COLORS["warning"])
        self.log_area.tag_config("ERROR", foreground=COLORS["danger"])
        self.log_area.tag_config("SUCCESS", foreground=COLORS["success"])
        self.log_area.tag_config("TIME", foreground="#52525b") # Zinc-600

        self.log_area.insert("1.0", f" {message}\n", level)
        self.log_area.insert("1.0", f"[{level}]", level)
        self.log_area.insert("1.0", f"{timestamp} ", "TIME")
        
        # Prevent memory leak by limiting log size to ~500 lines
        if int(self.log_area.index('end-1c').split('.')[0]) > 500:
            self.log_area.delete("500.0", "end")

    def build_header(self, parent_frame, title, subtitle=""):
        """Builds a consistent header for each content frame."""
        header_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        title_block = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_block.pack(side="left")
        ctk.CTkLabel(title_block, text=title, font=("Segoe UI Variable Display", 30, "bold")).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(title_block, text=subtitle, font=("Segoe UI", 12), text_color=COLORS["subtext"]).pack(anchor="w")

        if not hasattr(self, 'status_bar'):
            self.status_bar = ctk.CTkLabel(header_frame, text="  ●  System OK  ", font=("Segoe UI", 11, "bold"),
                                     fg_color=COLORS["card"], height=32, corner_radius=14, text_color=COLORS["success"])
            self.status_bar.pack(side="right", padx=10)

    def build_dashboard_frame(self):
        frame = self.content_frames["Dashboard"]

        # --- LAYOUT ---
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(0, weight=0) # Header
        frame.grid_rowconfigure(1, weight=0) # Graph
        frame.grid_rowconfigure(2, weight=1) # Actions

        # --- HEADER (Dashboard specific) ---
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        title_block = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_block.pack(side="left")
        ctk.CTkLabel(title_block, text="Dashboard", font=("Segoe UI Variable Display", 30, "bold")).pack(anchor="w")
        ctk.CTkLabel(title_block, text="Real-time system overview", font=("Segoe UI", 12), text_color=COLORS["subtext"]).pack(anchor="w")
        if not hasattr(self, 'status_bar'):
            self.status_bar = ctk.CTkLabel(header_frame, text="  ●  System OK  ", font=("Segoe UI", 11, "bold"),
                                     fg_color=COLORS["card"], height=32, corner_radius=14, text_color=COLORS["success"])
            self.status_bar.pack(side="right", padx=10)

        # --- GRAPH ---
        graph_card = self.create_card(frame, corner_radius=20)
        graph_card.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.setup_graph_widgets(graph_card)

        # --- QUICK ACTIONS ---
        actions_card = self.create_card(frame, corner_radius=20)
        actions_card.grid(row=2, column=0, sticky="nsew", padx=(0, 10))
        self.setup_quick_actions(actions_card)

        # --- SYSTEM INFO & EXTRAS ---
        info_card = self.create_card(frame, corner_radius=20)
        info_card.grid(row=2, column=1, sticky="nsew", padx=(10, 0))
        
        # Split info card into tabs or sections
        self.tabview = ctk.CTkTabview(info_card, fg_color="transparent", segmented_button_fg_color=COLORS["card"],
                                      segmented_button_selected_color=COLORS["accent"], segmented_button_selected_hover_color=COLORS["accent_hover"],
                                      segmented_button_unselected_hover_color=COLORS["glass_edge"],
                                      corner_radius=18)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=5)
        self.tabview.add("Overview")
        self.tabview.add("Storage & Net")
        self.setup_dashboard_overview(self.tabview.tab("Overview"))
        self.setup_dashboard_storage_net(self.tabview.tab("Storage & Net"))

    def setup_graph_widgets(self, parent_card):
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
        self.ax.grid(color="#2c2c2e", linestyle='-', linewidth=0.4, axis='y', alpha=0.6)
        self.fig.tight_layout(pad=0.5)

        self.cpu_line, = self.ax.plot(self.cpu_data, color=COLORS["accent"], lw=2.2, label="CPU", alpha=0.9)
        self.ram_line, = self.ax.plot(self.ram_data, color=COLORS["success"], lw=2.2, label="RAM", alpha=0.9)
        self.ax.legend(loc='upper left', frameon=False, fontsize=9, labelcolor=COLORS['text'], ncol=2)

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent_card)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="x", padx=10, pady=(0, 5))

    def setup_quick_actions(self, actions_card):
        self._build_card_header(actions_card, "⚡  Quick Actions", "One-tap tools for common tasks")

        # Real-time Sorter
        realtime_frame = ctk.CTkFrame(actions_card, fg_color="transparent")
        realtime_frame.pack(pady=5, padx=25, fill="x")
        rt_text = ctk.CTkFrame(realtime_frame, fg_color="transparent")
        rt_text.pack(side="left")
        ctk.CTkLabel(rt_text, text="Auto-Clean Desktop", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ctk.CTkLabel(rt_text, text="Sort new files in real-time", font=("Segoe UI", 11), text_color=COLORS["subtext"]).pack(anchor="w")
        self.realtime_switch = ctk.CTkSwitch(realtime_frame, text="", command=self.toggle_realtime_sort,
                                             progress_color=COLORS["accent"], button_color="#636366",
                                             fg_color=COLORS["border"], button_hover_color=COLORS["glass_edge"])
        self.realtime_switch.pack(side="right")

        ctk.CTkFrame(actions_card, fg_color=COLORS["border"], height=1).pack(fill="x", padx=25, pady=10)

        self.btn_hide = self.create_button(actions_card, "Incognito: Hide Icons", "tinted", self.toggle_icons)
        self.btn_hide.pack(pady=(0, 8), padx=25, fill="x")
        self.create_button(actions_card, "Purge Clipboard", "secondary", self.purge_clip).pack(pady=(0, 15), padx=25, fill="x")

    def setup_dashboard_overview(self, parent):
        sys_info = self.get_system_info()
        info_to_show = {
            "OS": sys_info["os"],
            "CPU": sys_info["cpu"],
            "RAM": sys_info["ram"],
            "Uptime": self.get_uptime()
        }

        for i, (key, value) in enumerate(info_to_show.items()):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=key, font=("Segoe UI", 13, "bold"), text_color=COLORS["subtext"], width=80, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, font=("Segoe UI", 13), anchor="w").pack(side="left", fill="x", expand=True)

    def setup_dashboard_storage_net(self, parent):
        # Disk Usage
        ctk.CTkLabel(parent, text="Disk Usage (C:)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(10, 5))
        self.disk_bar = ctk.CTkProgressBar(parent, height=15, corner_radius=8, progress_color=COLORS["accent"])
        self.disk_bar.pack(fill="x", pady=(0, 5))
        self.disk_label = ctk.CTkLabel(parent, text="Calculating...", font=("Segoe UI", 11), text_color=COLORS["subtext"])
        self.disk_label.pack(anchor="e")

        # Network Latency
        ctk.CTkLabel(parent, text="Network Latency (8.8.8.8)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(15, 5))
        self.ping_label = ctk.CTkLabel(parent, text="-- ms", font=("Segoe UI Variable Display", 24, "bold"), text_color=COLORS["success"])
        self.ping_label.pack(anchor="center", pady=5)

    def update_dashboard_extras(self):
        # 1. Update Disk
        try:
            usage = shutil.disk_usage("C:\\")
            percent = (usage.used / usage.total)
            self.disk_bar.set(percent)
            self.disk_label.configure(text=f"{percent*100:.1f}% Used of {usage.total // (1024**3)} GB")
        except: pass

        # 2. Update Ping (Threaded)
        def _ping():
            try:
                # Use socket for much faster/lighter ping
                t1 = time.time()
                socket.create_connection(("8.8.8.8", 53), timeout=2).close()
                latency = int((time.time() - t1) * 1000)
                if latency < 1: latency = 1
                color = COLORS["success"] if latency < 50 else COLORS["warning"] if latency < 150 else COLORS["danger"]
                self.after(0, lambda: self.ping_label.configure(text=f"{latency} ms", text_color=color))
            except:
                self.after(0, lambda: self.ping_label.configure(text="Timeout", text_color="red"))
        
        if self.ping_thread is None or not self.ping_thread.is_alive():
            self.ping_thread = threading.Thread(target=_ping, daemon=True)
            self.ping_thread.start()

        self.after(5000, self.update_dashboard_extras)

    def get_uptime(self):
        try:
            delta = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
            return str(delta).split('.')[0] # Remove microseconds
        except: return "Unknown"


    def build_sysinfo_frame(self):
        frame = self.content_frames["Sys Info"]
        self.build_header(frame, "System Information", "Hardware and software details for this machine")

        scroll_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent",
                                              scrollbar_fg_color=COLORS["bg"],
                                              scrollbar_button_color=COLORS["border"], scrollbar_button_hover_color=COLORS["glass_edge"])
        self._style_scrollable(scroll_frame)
        scroll_frame.pack(fill="both", expand=True, padx=10)

        # Gather System Info
        sys_info = self.get_system_info()

        info_list = [
            ("Hostname", sys_info["hostname"]),
            ("Operating System", sys_info["os_full"]),
            ("CPU Model", sys_info["cpu"]),
            ("Total RAM", sys_info["ram"]),
            ("Python Version", sys_info["python_version"])
        ]

        for label, value in info_list:
            card = self.create_card(scroll_frame, corner_radius=15)
            card.pack(fill="x", pady=8, padx=10)
            ctk.CTkLabel(card, text=label, font=("Segoe UI", 14, "bold"), text_color=COLORS["subtext"]).pack(side="left", padx=20, pady=15)
            ctk.CTkLabel(card, text=value, font=("Segoe UI", 14, "bold")).pack(side="right", padx=20, pady=15)

    def build_installer_frame(self):
        frame = self.content_frames["Installer"]
        self.build_header(frame, "Software Installer", "Install common apps via Windows Package Manager (winget)")

        if not is_winget_available():
            ctk.CTkLabel(frame, text="⚠️ Windows Package Manager (winget) not found.\nThis feature is unavailable.",
                         font=("Segoe UI", 16), text_color="orange").pack(expand=True)
            self.log_message("Winget not found, installer disabled.", "WARN")
            return

        scroll_frame = ctk.CTkScrollableFrame(frame, fg_color=COLORS["card"], border_width=1, border_color=COLORS["border"], corner_radius=22,
                                              scrollbar_fg_color=COLORS["card"],
                                              scrollbar_button_color=COLORS["border"], scrollbar_button_hover_color=COLORS["glass_edge"])
        self._style_scrollable(scroll_frame)
        scroll_frame.pack(fill="both", expand=True)

        def _populate_installer():
            self.installed_software_ids = check_installed_software()
            self.log_message(f"Found {len(self.installed_software_ids)} installed packages via winget.")

            for name, app_id in SOFTWARE_TO_INSTALL.items():
                app_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                app_frame.pack(fill="x", padx=20, pady=10)
                
                ctk.CTkLabel(app_frame, text=name, font=("Segoe UI", 14, "bold")).pack(side="left", padx=(0, 10))
                
                if app_id in self.installed_software_ids:
                    ctk.CTkLabel(app_frame, text="Installed", font=("Segoe UI", 12, "bold"), text_color=COLORS["success"]).pack(side="right", padx=10)
                else:
                    # Frame to hold the dynamic widgets
                    action_frame = ctk.CTkFrame(app_frame, fg_color="transparent")
                    action_frame.pack(side="right", fill="x", expand=True)

                    status_label = ctk.CTkLabel(action_frame, text="", font=("Segoe UI", 12), text_color=COLORS["subtext"])
                    status_label.pack(side="right", padx=10)

                    progress_bar = ctk.CTkProgressBar(action_frame, orientation="horizontal", indeterminate_speed=1.2)

                    install_btn = self.create_button(action_frame, "Install", "secondary", 
                                                     lambda id=app_id, af=action_frame, s=status_label, b=None, p=progress_bar: self.install_software(id, af, s, b, p))
                    # A bit of a hack to pass the button to itself for disabling
                    install_btn.configure(command=lambda id=app_id, af=action_frame, s=status_label, b=install_btn, p=progress_bar: self.install_software(id, af, s, b, p))
                    install_btn.pack(side="right")

        # Run the check in a separate thread to not freeze the UI on startup
        threading.Thread(target=_populate_installer, daemon=True).start()

    def install_software(self, app_id, action_frame, status_label, button, progress_bar):
        """Starts a thread to install software using winget."""
        # Hide the button and show the progress bar
        button.pack_forget()

        button.configure(state="disabled")
        status_label.configure(text="Installing...", text_color=COLORS["accent"])
        progress_bar.pack(side="right", padx=10, fill="x", expand=True)
        progress_bar.start()
        self.log_message(f"Starting install for {app_id}")

        def _worker():
            app_frame = action_frame.master # Get parent frame
            try:
                command = ["winget", "install", "--id", app_id, "-e", "--accept-package-agreements", "--accept-source-agreements"]
                result = subprocess.run(command, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
                
                self.after(0, self.on_install_success, app_frame, action_frame)
                self.log_message(f"Successfully installed {app_id}", "SUCCESS")
            except subprocess.CalledProcessError as e:
                self.after(0, self.on_install_failure, status_label, button, progress_bar)
                self.log_message(f"Failed to install {app_id}. Error: {e.stderr}", "ERROR")
            except FileNotFoundError:
                self.after(0, self.on_install_failure, status_label, button, progress_bar)
                self.log_message("Winget command not found during install.", "ERROR")

        threading.Thread(target=_worker, daemon=True).start()

    def on_install_success(self, app_frame, action_frame):
        """Called on UI thread after successful software installation."""
        action_frame.destroy()
        ctk.CTkLabel(app_frame, text="Installed", font=("Segoe UI", 12, "bold"), text_color=COLORS["success"]).pack(side="right", padx=10)

    def on_install_failure(self, status_label, button, progress_bar):
        """Called on UI thread after failed software installation."""
        progress_bar.stop()
        progress_bar.pack_forget()
        status_label.configure(text="Failed", text_color="red")
        button.pack(side="right")
        button.configure(state="normal")

    def build_tools_frame(self):
        frame = self.content_frames["Tools"]
        self.build_header(frame, "Service Desk Tools", "Common fixes and utilities for everyday IT support")

        tab_view = ctk.CTkTabview(frame, fg_color="transparent",
                                  segmented_button_fg_color=COLORS["card"],
                                  segmented_button_selected_color=COLORS["accent"],
                                  segmented_button_unselected_color=COLORS["card"],
                                  segmented_button_selected_hover_color=COLORS["accent_hover"],
                                  segmented_button_unselected_hover_color=COLORS["glass_edge"],
                                  corner_radius=18, border_width=0)
        tab_view.pack(fill="both", expand=True, padx=0, pady=10)

        # Add tabs for each category
        tab_view.add("Cleanup")
        tab_view.add("Network")
        tab_view.add("System & Power")
        tab_view.add("Shortcuts")

        # Populate each tab with its respective tools
        self._build_tools_cleanup_tab(tab_view.tab("Cleanup"))
        self._build_tools_network_tab(tab_view.tab("Network"))
        self._build_tools_system_tab(tab_view.tab("System & Power"))
        self._build_tools_shortcuts_tab(tab_view.tab("Shortcuts"))

    def _create_tools_tab_scroller(self, parent_tab):
        """Helper to create a consistent scrollable frame for tool tabs. Scrollbar styled and auto-hidden when possible."""
        scroll_frame = ctk.CTkScrollableFrame(parent_tab, fg_color="transparent",
                                              scrollbar_fg_color=COLORS["bg"],
                                              scrollbar_button_color=COLORS["border"], scrollbar_button_hover_color=COLORS["glass_edge"])
        self._style_scrollable(scroll_frame)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=0)
        scroll_frame.grid_columnconfigure(0, weight=1)
        scroll_frame.grid_columnconfigure(1, weight=1)
        return scroll_frame

    def _build_tools_cleanup_tab(self, tab):
        scroll_frame = self._create_tools_tab_scroller(tab)

        # --- Folder Cleanup ---
        folder_card = self.create_card(scroll_frame)
        folder_card.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")
        self._build_card_header(folder_card, "📁  Folder Cleanup", "Auto-sort loose files into organized category folders")
        self.create_button(folder_card, "Clean Desktop", "primary", self.perform_sort).pack(pady=(0, 5), padx=25, fill="x")
        self.create_button(folder_card, "Clean Downloads Folder", "primary", self.perform_downloads_sort).pack(pady=(5, 15), padx=25, fill="x")

        # --- System Cleanup ---
        system_card = self.create_card(scroll_frame)
        system_card.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="nsew")
        self._build_card_header(system_card, "🧹  System Cleanup", "Free space and fix common Office sign-in issues")
        self.create_button(system_card, "Clean Temporary Files", "secondary", self.clean_temp_files).pack(pady=(0, 5), padx=25, fill="x")
        self.create_button(system_card, "Reset M365 Credentials", "danger", self.clean_m365_credentials).pack(pady=(5, 15), padx=25, fill="x")

        # --- Cache & Bin ---
        cache_card = self.create_card(scroll_frame)
        cache_card.grid(row=1, column=0, padx=(0, 10), pady=10, sticky="nsew")
        self._build_card_header(cache_card, "🗑️  Cache & Recycle Bin", "Clear system caches and free up storage space")
        self.create_button(cache_card, "Clear Windows Update Cache", "danger", self.clear_update_cache).pack(pady=(0, 5), padx=25, fill="x")
        self.create_button(cache_card, "Clear Delivery Optimization Cache", "danger", self.clear_delivery_optimization).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(cache_card, "Clear Windows Error Reports", "secondary", self.clear_windows_error_reports).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(cache_card, "Clear Icon Cache", "danger", self.clear_icon_cache).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(cache_card, "Clear Prefetch Cache", "danger", self.clear_prefetch).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(cache_card, "Empty Recycle Bin", "danger", self.empty_recycle_bin).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(cache_card, "Clear Browser Cache (Edge/Chrome)", "secondary", self.clear_browser_cache).pack(pady=(5, 15), padx=25, fill="x")

        # --- File Utilities ---
        file_card = self.create_card(scroll_frame)
        file_card.grid(row=1, column=1, padx=(10, 0), pady=10, sticky="nsew")
        self._build_card_header(file_card, "🔐  File Utilities", "Verify file integrity with cryptographic hashes")
        self.create_button(file_card, "Calculate File Hash (SHA256)", "secondary", self.calc_file_hash).pack(pady=(0, 15), padx=25, fill="x")

    def _build_tools_network_tab(self, tab):
        scroll_frame = self._create_tools_tab_scroller(tab)

        # --- Basic Network Tools ---
        basic_card = self.create_card(scroll_frame)
        basic_card.grid(row=0, column=0, columnspan=2, padx=0, pady=10, sticky="ew")
        self._build_card_header(basic_card, "🌐  Network Diagnostics", "Quick fixes for internet and connectivity problems")
        self.create_button(basic_card, "Flush DNS Cache", "secondary", self.flush_dns).pack(pady=(0, 5), padx=25, fill="x")
        self.create_button(basic_card, "Reset Winsock", "secondary", self.reset_winsock).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(basic_card, "Reset Network Stack (IP)", "secondary", self.reset_network_stack).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(basic_card, "Release & Renew IP", "secondary", self.release_renew_ip).pack(pady=(5, 15), padx=25, fill="x")

        # --- Advanced Network Tools ---
        adv_card = self.create_card(scroll_frame)
        adv_card.grid(row=1, column=0, columnspan=2, padx=0, pady=10, sticky="ew")
        self._build_card_header(adv_card, "🔍  Advanced Network", "IP lookup, WiFi recovery, and DNS configuration")
        self.create_button(adv_card, "Show External IP", "secondary", self.show_external_ip).pack(pady=(0, 5), padx=25, fill="x")
        self.create_button(adv_card, "Reveal WiFi Passwords", "danger", self.reveal_wifi_passwords).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(adv_card, "Restart WLAN Service", "secondary", self.restart_wlan_service).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(adv_card, "Set DNS to Google (8.8.8.8)", "secondary", lambda: self.set_dns("8.8.8.8")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(adv_card, "Set DNS to Cloudflare (1.1.1.1)", "secondary", lambda: self.set_dns("1.1.1.1")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(adv_card, "Set DNS to Automatic (DHCP)", "secondary", self.set_dns_automatic).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(adv_card, "Open Network Reset (Full Reset)", "secondary", self.network_reset_full).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(adv_card, "Run Network Troubleshooter", "secondary", self.run_network_troubleshooter).pack(pady=(5, 15), padx=25, fill="x")

    def _build_tools_system_tab(self, tab):
        scroll_frame = self._create_tools_tab_scroller(tab)

        # --- Repair & Maintenance ---
        repair_card = self.create_card(scroll_frame)
        repair_card.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")
        self._build_card_header(repair_card, "🔧  Repair & Maintenance", "Scan and repair Windows system files and images")
        self.create_button(repair_card, "Run System File Checker (SFC)", "danger", self.run_sfc_scan).pack(pady=(0, 5), padx=25, fill="x")
        self.create_button(repair_card, "Repair Windows Image (DISM)", "danger", self.run_dism_scan).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(repair_card, "Create System Restore Point", "danger", self.create_restore_point).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(repair_card, "Check Disk (Read-Only)", "secondary", lambda: self.open_shell_command("start cmd /k chkdsk C:")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(repair_card, "Open Disk Management", "secondary", lambda: self.open_sys_tool("diskmgmt.msc")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(repair_card, "Run Disk Cleanup", "secondary", self.run_disk_cleanup).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(repair_card, "Sync Windows Time", "secondary", self.sync_time_windows).pack(pady=(5, 15), padx=25, fill="x")

        # --- Power Management ---
        power_card = self.create_card(scroll_frame)
        power_card.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="nsew")
        self._build_card_header(power_card, "⚡  Power Management", "Battery reports, shutdown scheduling, and hibernation")
        self.create_button(power_card, "Generate Battery Report", "secondary", self.generate_battery_report).pack(pady=(0, 5), padx=25, fill="x")
        self.create_button(power_card, "Schedule Shutdown (1 Hour)", "secondary", lambda: self.schedule_shutdown(3600)).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(power_card, "Abort Shutdown", "secondary", lambda: self.run_command(["shutdown", "/a"], "Shutdown Cancelled")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(power_card, "Disable Hibernation", "danger", lambda: self.run_command(["powercfg.exe", "/hibernate", "off"], "Hibernation Disabled")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(power_card, "Enable Hibernation", "secondary", lambda: self.run_command(["powercfg.exe", "/hibernate", "on"], "Hibernation Enabled")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(power_card, "Turn Off Monitor", "secondary", self.turn_off_monitor).pack(pady=(5, 15), padx=25, fill="x")

        # --- Processes & Services ---
        proc_card = self.create_card(scroll_frame)
        proc_card.grid(row=1, column=0, padx=(0, 10), pady=10, sticky="nsew")
        self._build_card_header(proc_card, "⚙️  Processes & Services", "Restart stuck services like Print Spooler or Explorer")
        self.create_button(proc_card, "Restart Print Spooler", "secondary", self.restart_spooler).pack(pady=(0, 5), padx=25, fill="x")
        self.create_button(proc_card, "Restart Audio Service", "secondary", self.restart_audio_service).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(proc_card, "Restart Explorer.exe", "danger", self.restart_explorer).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(proc_card, "Task Scheduler", "secondary", self.open_task_scheduler).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(proc_card, "Reliability Monitor", "secondary", self.reliability_monitor).pack(pady=(5, 15), padx=25, fill="x")

        # --- Windows Settings ---
        win_card = self.create_card(scroll_frame)
        win_card.grid(row=1, column=1, padx=(10, 0), pady=10, sticky="nsew")
        self._build_card_header(win_card, "🪟  Windows Settings", "Quick links to common Windows settings pages")
        self.create_button(win_card, "Check for Windows Updates", "secondary", lambda: self.open_shell_command("start ms-settings:windowsupdate")).pack(pady=(0, 5), padx=25, fill="x")
        self.create_button(win_card, "Open Startup Apps", "secondary", lambda: self.open_shell_command("start ms-settings:startupapps")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(win_card, "Open Windows Security", "secondary", lambda: self.open_shell_command("start ms-settings:windowsdefender")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(win_card, "Open Sound Settings", "secondary", lambda: self.open_shell_command("start ms-settings:sound")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(win_card, "Open Display Settings", "secondary", lambda: self.open_shell_command("start ms-settings:display")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(win_card, "Open Storage Settings", "secondary", lambda: self.open_shell_command("start ms-settings:storagestorage")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(win_card, "Optional Features", "secondary", lambda: self.open_shell_command("start ms-settings:optionalfeatures")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(win_card, "Default Apps", "secondary", lambda: self.open_shell_command("start ms-settings:defaultapps")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(win_card, "Printers & Scanners", "secondary", lambda: self.open_shell_command("start ms-settings:printers")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(win_card, "Bluetooth", "secondary", lambda: self.open_shell_command("start ms-settings:bluetooth")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(win_card, "Notifications", "secondary", lambda: self.open_shell_command("start ms-settings:notifications")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(win_card, "Troubleshoot (Settings)", "secondary", lambda: self.open_shell_command("start ms-settings:troubleshoot")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(win_card, "About (PC Info)", "secondary", lambda: self.open_shell_command("start ms-settings:about")).pack(pady=(5, 15), padx=25, fill="x")

    def _build_tools_shortcuts_tab(self, tab):
        scroll_frame = self._create_tools_tab_scroller(tab)

        # --- Common Tools ---
        common_card = self.create_card(scroll_frame)
        common_card.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")
        self._build_card_header(common_card, "🖥️  Common Tools", "Frequently used Windows management utilities")
        self.create_button(common_card, "Task Manager", "secondary", lambda: self.open_sys_tool("taskmgr")).pack(pady=(0, 5), padx=25, fill="x")
        self.create_button(common_card, "Control Panel", "secondary", lambda: self.open_sys_tool("control")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(common_card, "Registry Editor", "secondary", lambda: self.open_sys_tool("regedit")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(common_card, "System Information", "secondary", lambda: self.open_sys_tool("msinfo32")).pack(pady=(5, 15), padx=25, fill="x")

        # --- Admin & Management ---
        admin_card = self.create_card(scroll_frame)
        admin_card.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="nsew")
        self._build_card_header(admin_card, "🛡️  Admin & Management", "Administrative consoles — require elevated privileges")
        self.create_button(admin_card, "Group Policy Editor", "secondary", lambda: self.open_sys_tool("gpedit.msc")).pack(pady=(0, 5), padx=25, fill="x")
        self.create_button(admin_card, "Services", "secondary", lambda: self.open_sys_tool("services.msc")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(admin_card, "Device Manager", "secondary", lambda: self.open_sys_tool("devmgmt.msc")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(admin_card, "Event Viewer", "secondary", lambda: self.open_sys_tool("eventvwr.msc")).pack(pady=(5, 15), padx=25, fill="x")

        # --- System Properties ---
        props_card = self.create_card(scroll_frame)
        props_card.grid(row=1, column=0, padx=(0, 10), pady=10, sticky="nsew")
        self._build_card_header(props_card, "🔗  System Properties", "Network, program, and system configuration panels")
        self.create_button(props_card, "Network Connections", "secondary", lambda: self.open_sys_tool("ncpa.cpl")).pack(pady=(0, 5), padx=25, fill="x")
        self.create_button(props_card, "Programs & Features", "secondary", lambda: self.open_sys_tool("appwiz.cpl")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(props_card, "System Properties", "secondary", lambda: self.open_sys_tool("sysdm.cpl")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(props_card, "Power Options", "secondary", lambda: self.open_sys_tool("powercfg.cpl")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(props_card, "Date and Time", "secondary", lambda: self.open_sys_tool("timedate.cpl")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(props_card, "Mouse Properties", "secondary", lambda: self.open_sys_tool("main.cpl")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(props_card, "Run Dialog", "secondary", lambda: self.open_shell_command("explorer shell:::{2559a1f3-21d7-11d4-bdaf-00c04f60b9f0}")).pack(pady=(5, 15), padx=25, fill="x")

        # --- Monitors & Cleanup ---
        monitor_card = self.create_card(scroll_frame)
        monitor_card.grid(row=1, column=1, padx=(10, 0), pady=10, sticky="nsew")
        self._build_card_header(monitor_card, "📈  Monitors & Security", "Performance monitoring, disk cleanup, and BitLocker")
        self.create_button(monitor_card, "Resource Monitor", "secondary", lambda: self.open_sys_tool("resmon")).pack(pady=(0, 5), padx=25, fill="x")
        self.create_button(monitor_card, "Performance Monitor", "secondary", lambda: self.open_sys_tool("perfmon")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(monitor_card, "Computer Management", "secondary", lambda: self.open_sys_tool("compmgmt.msc")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(monitor_card, "Certificate Manager", "secondary", lambda: self.open_sys_tool("certmgr.msc")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(monitor_card, "Print Management", "secondary", lambda: self.open_sys_tool("printmanagement.msc")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(monitor_card, "Disk Cleanup", "secondary", lambda: self.open_sys_tool("cleanmgr.exe")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(monitor_card, "Disk Management", "secondary", lambda: self.open_sys_tool("diskmgmt.msc")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(monitor_card, "Windows Memory Diagnostic", "secondary", lambda: self.open_sys_tool("mdsched.exe")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(monitor_card, "ODBC Data Sources", "secondary", lambda: self.open_sys_tool("odbcad32.exe")).pack(pady=(5, 5), padx=25, fill="x")
        self.create_button(monitor_card, "Get BitLocker Keys", "secondary", self.get_bitlocker_keys).pack(pady=(5, 15), padx=25, fill="x")

    def build_file_scanner_frame(self):
        frame = self.content_frames["File Scanner"]
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # --- HEADER (Apple-style: large title + soft subtitle) ---
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 24))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Storage", font=("Segoe UI Variable Display", 34, "bold"), text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="Find large files and folders taking up space on your drive.", font=("Segoe UI", 13),
                     text_color=COLORS["subtext"]).grid(row=1, column=0, sticky="w", pady=(6, 0))

        # --- SCAN CARD (glass panel with clear hierarchy) ---
        control_frame = ctk.CTkFrame(frame, fg_color=COLORS["card"], corner_radius=20, border_width=1, border_color=COLORS["border"])
        control_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 16))
        control_frame.grid_columnconfigure(1, weight=1)

        # Top: title + subtitle inside card
        card_header = ctk.CTkFrame(control_frame, fg_color="transparent")
        card_header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=24, pady=(20, 8))
        card_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card_header, text="Scan for large files", font=("Segoe UI Variable Display", 18, "bold"), text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(card_header, text="Choose a drive and run a scan to list the biggest items.", font=("Segoe UI", 12),
                     text_color=COLORS["subtext"]).grid(row=1, column=0, sticky="w", pady=(2, 0))

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
                                                   fg_color=COLORS["border"], mode="indeterminate", indeterminate_speed=1.2)
        self.scan_progress_bar.grid(row=2, column=0, columnspan=3, sticky="ew", padx=24, pady=(0, 20))
        self.scan_progress_bar.grid_remove()

        # --- RESULTS (Apple-style list container) ---
        results_wrapper = ctk.CTkFrame(frame, fg_color="transparent")
        results_wrapper.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        results_wrapper.grid_rowconfigure(1, weight=1)
        results_wrapper.grid_columnconfigure(0, weight=1)

        results_label_row = ctk.CTkFrame(results_wrapper, fg_color="transparent")
        results_label_row.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        results_label_row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(results_label_row, text="Results", font=("Segoe UI Variable Display", 15, "bold"), text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")

        tree_card = ctk.CTkFrame(results_wrapper, fg_color=COLORS["card"], corner_radius=16, border_width=1, border_color=COLORS["border"])
        tree_card.grid(row=1, column=0, sticky="nsew")
        tree_card.grid_rowconfigure(1, weight=1)
        tree_card.grid_columnconfigure(0, weight=1)

        # Column header bar (subtle, like Finder)
        col_header = ctk.CTkFrame(tree_card, fg_color=COLORS["bg"], height=36, corner_radius=0)
        col_header.grid(row=0, column=0, columnspan=2, sticky="ew")
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
        self.scan_progress_bar.grid(row=2, column=0, columnspan=3, sticky="ew", padx=24, pady=(0, 20))
        self.scan_progress_bar.start()
        if hasattr(self, "scanner_empty_label"):
            self.scanner_empty_label.place_forget()

        self.log_message(f"Starting disk space scan for {drive_to_scan}")
        
        thread = threading.Thread(target=self._scan_directory_worker, args=(drive_to_scan,), daemon=True)
        thread.start()

    def build_logs_frame(self):
        frame = self.content_frames["Logs"]
        self.build_header(frame, "Activity Logs", "Timestamped record of all actions performed in this session")
        log_frame = ctk.CTkFrame(frame, fg_color=COLORS["card"], border_width=1, border_color=COLORS["border"], corner_radius=20)
        log_frame.pack(pady=10, padx=25, fill="both", expand=True)
        self.log_area = ctk.CTkTextbox(log_frame, fg_color=COLORS["bg"], font=("Cascadia Code", 11), border_width=0, corner_radius=18)
        self.log_area.pack(pady=4, padx=4, fill="both", expand=True)

    def build_settings_frame(self):
        frame = self.content_frames["Settings"]
        self.build_header(frame, "Settings", "Customize file sorting rules and appearance")

        scroll_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent",
                                              scrollbar_fg_color=COLORS["bg"],
                                              scrollbar_button_color=COLORS["border"], scrollbar_button_hover_color=COLORS["glass_edge"])
        scroll_frame.pack(fill="both", expand=True, padx=20)

        ctk.CTkLabel(scroll_frame, text="Desktop Cleaning Categories", font=("Segoe UI", 15, "bold")).pack(pady=(0, 10), anchor="w")
        ctk.CTkLabel(scroll_frame, text="Define which file extensions belong to each category. Separate extensions with a comma.",
                     font=("Segoe UI", 12), text_color=COLORS["subtext"], wraplength=600).pack(pady=(0, 20), anchor="w")

        self.settings_entries = {}
        for category, extensions in self.rules.items():
            card = self.create_card(scroll_frame, corner_radius=12)
            card.pack(pady=6, fill="x", expand=True)

            card.grid_columnconfigure(1, weight=1)

            label = ctk.CTkLabel(card, text=category, font=("Segoe UI", 14, "bold"))
            label.grid(row=0, column=0, padx=20, pady=15, sticky="w")

            ext_string = ", ".join(extensions)
            entry = ctk.CTkEntry(card, font=("Consolas", 12), border_color=COLORS["border"])
            entry.insert(0, ext_string)
            entry.grid(row=0, column=1, padx=20, pady=15, sticky="ew")
            self.settings_entries[category] = entry

        # Theme Toggle
        self.create_button(frame, "Toggle Dark/Light Mode", "secondary", self.toggle_theme).pack(pady=10, padx=20, fill="x")

        save_button = self.create_button(frame, "Save All Settings", "primary", self.save_all_settings)
        save_button.pack(pady=20, padx=20, fill="x")

    def save_all_settings(self):
        try:
            for category, entry in self.settings_entries.items():
                ext_text = entry.get()
                # Sanitize: remove spaces, split by comma, filter empty strings, ensure dot prefix
                new_exts = [f".{ext.strip().lstrip('.')}" for ext in ext_text.split(',') if ext.strip()]
                self.rules[category] = sorted(list(set(new_exts))) # Sort and remove duplicates
            
            self.save_config()
            self.log_message("Settings saved successfully.")
            self.show_notification("Settings Saved!", COLORS["success"])
        except Exception as e:
            self.log_message(f"Error saving settings: {e}", "ERROR")
            self.show_notification("Error saving settings", "red")

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)

    def create_card(self, parent, corner_radius=22):
        frame = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=corner_radius, border_width=1, border_color=COLORS["border"])
        return frame

    def create_button(self, parent, text, style, cmd):
        return ctk.CTkButton(parent, text=text, command=cmd,
                             corner_radius=18, height=42, font=("Segoe UI", 13, "bold"),
                             **self.button_styles.get(style, self.button_styles["secondary"]))

    def _build_card_header(self, card, title, subtitle=""):
        """Builds a card header with title and optional subtitle for 1st-level tech context."""
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 15, "bold")).pack(pady=(15, 2), padx=25, anchor="w")
        if subtitle:
            ctk.CTkLabel(card, text=subtitle, font=("Segoe UI", 11), text_color=COLORS["subtext"]).pack(pady=(0, 10), padx=25, anchor="w")

    def on_closing(self):
        """Handles window close event to safely stop the observer."""
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        self.destroy()

    def _on_window_resize(self, event):
        # Only reposition if the height or width changed, and it's the root window
        if event.widget == self and (event.width != self.winfo_width() or event.height != self.winfo_height()):
            self._reposition_notifications()
    def get_system_info(self):
        """Gathers and returns a dictionary of key system information."""
        try:
            uname = platform.uname()
            os_info = f"{uname.system} {uname.release}"
            os_info_full = f"{uname.system} {uname.release} ({uname.version})"
            node_name = uname.node
        except:
            os_info = "Unknown"
            os_info_full = "Unknown"
            node_name = "Unknown"

        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            cpu_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            winreg.CloseKey(key)
            cpu_name = cpu_name.strip()
        except:
            cpu_name = platform.processor()

        ram_gb = f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB"
        
        return {
            "hostname": node_name, "os": os_info, "os_full": os_info_full,
            "cpu": cpu_name, "ram": ram_gb, "python_version": sys.version.split()[0]
        }

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
                # If internal attributes change in CustomTkinter, fail silently
                pass

        try:
            scroll_frame._scrollable_frame.bind("<Configure>", _update)
            scroll_frame.bind("<Configure>", _update)
            self.after(100, _update)
        except Exception:
            pass

    def _reposition_notifications(self):
        """Recalculates and sets the y-position for all active toasts."""
        center_x = (self.winfo_width() - NOTIFICATION_WIDTH) // 2
        current_y_offset = NOTIFICATION_MARGIN_Y
        # Iterate in reverse to position from bottom up
        for toast_info in reversed(self.active_toasts):
            # Calculate target y position from the bottom of the window
            toast_info["y_pos"] = self.winfo_height() - current_y_offset - toast_info["height"]
            toast_info["target_x"] = center_x
            # Update its position if it's already placed
            if toast_info["widget"].winfo_ismapped():
                toast_info["widget"].place(y=toast_info["y_pos"], x=center_x)
            
            current_y_offset += toast_info["height"] + NOTIFICATION_SPACING

    def _animate_toast_in(self, toast_info):
        """Animates a toast sliding up from bottom."""
        # Simplified: Just place it for now to avoid complex coordinate math bugs
        toast_info["widget"].place(x=toast_info["target_x"], y=toast_info["y_pos"])
        # Opacity animation is hard in tk, so we just slide up if we want, but direct placement is safer for "glitchy" reports

    def _animate_toast_out(self, toast_info):
        """Destroys the toast."""
        self.active_toasts = [t for t in self.active_toasts if t["id"] != toast_info["id"]]
        toast_info["widget"].destroy()
        self.after(0, self._reposition_notifications)

    def show_notification(self, message, color=COLORS["accent"], duration=3000):
        """Displays an animated toast notification."""
        toast_id = self.notification_counter
        self.notification_counter += 1

        toast = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=20, border_width=1, border_color=color, width=NOTIFICATION_WIDTH)
        toast.lift()

        inner = ctk.CTkFrame(toast, fg_color="transparent")
        inner.pack(padx=16, pady=12, fill="both", expand=True)
        dot = ctk.CTkLabel(inner, text="●", font=("Segoe UI", 10), text_color=color, width=16)
        dot.pack(side="left", padx=(0, 8))
        label = ctk.CTkLabel(inner, text=message, font=("Segoe UI", 13, "bold"), text_color=COLORS["text"], wraplength=NOTIFICATION_WIDTH - 60, anchor="w")
        label.pack(side="left", fill="both", expand=True)
        
        self.update_idletasks() # Ensure label and toast dimensions are calculated
        toast_height = toast.winfo_reqheight() # Get actual required height
        
        center_x = (self.winfo_width() - NOTIFICATION_WIDTH) // 2

        toast_info = {
            "id": toast_id,
            "widget": toast,
            "target_x": center_x,
            "current_x": center_x,
            "height": toast_height # Use actual height
        }
        self.active_toasts.append(toast_info)
        
        self._reposition_notifications() # Position all toasts, including the new one
        
        self._animate_toast_in(toast_info)

        # Schedule destruction
        self.after(duration, lambda: self._animate_toast_out(toast_info))

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
            run_as_admin()
            return False # New process starts, old one should not proceed
        return True # User chose No, proceed without admin

    def update_vitals(self):
        # Get data
        cpu_percent = psutil.cpu_percent()
        ram_percent = psutil.virtual_memory().percent

        # Update data deques
        self.cpu_data.append(cpu_percent)
        self.ram_data.append(ram_percent)

        self.cpu_label.configure(text=f"CPU  {cpu_percent:.1f}%")
        self.ram_label.configure(text=f"RAM  {ram_percent:.1f}%")

        bat = psutil.sensors_battery()
        if bat: self.bat_label.configure(text=f"BAT {bat.percent}%")

        # Update graph
        if self.content_frames["Dashboard"].winfo_viewable():
            self.update_graph()

        self.after(2000, self.update_vitals)

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
            self.show_notification("Real-time Cleaning Activated", COLORS["success"])
        else:
            if self.observer.is_alive():
                self.observer.stop()
                self.observer.join()
            self.show_notification("Real-time Cleaning Deactivated", COLORS["subtext"])

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
            self.show_notification(f"Incognito Mode {status}", COLORS["accent"])
        except Exception as e:
            self.show_notification("Error Toggling Icons", "red")
            print(f"Icon Toggle Error: {e}")

    def purge_clip(self):
        """Clears the system clipboard."""
        pyperclip.copy("")
        self.log_message("Clipboard purged.")
        self.show_notification("Clipboard Purged", COLORS["success"])

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

        self.show_notification("Resetting M365 Credentials...", COLORS["accent"])
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
        self.show_notification("M365 Reset Complete — Sign in again to continue", COLORS["success"])

    def create_restore_point(self):
        if not self.prompt_for_admin("Create Restore Point"):
            return
        if not messagebox.askyesno("Confirm", "This will create a system restore point. This may take a few moments. Continue?"):
            return
        
        self.log_message("Creating system restore point...")
        self.show_notification("Creating Restore Point...", COLORS["accent"])
        
        # Use PowerShell to create the restore point. This is the most reliable way.
        command = 'powershell.exe -ExecutionPolicy Bypass -NoProfile -Command "Checkpoint-Computer -Description \'Ombra_Utility_Restore_Point\' -RestorePointType \'MODIFY_SETTINGS\'"'
        
        def _worker():
            try:
                # Using CREATE_NO_WINDOW to hide the PowerShell window
                subprocess.run(command, check=True, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                self.after(0, lambda: self.show_notification("Restore Point Created Successfully", COLORS["success"]))
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
                    self.after(0, lambda: self.show_notification("Failed to Create Restore Point", "red"))
                    self.log_message(f"Failed to create restore point: {error_message}", "ERROR")
            except Exception as e:
                self.after(0, lambda: self.show_notification("Failed to Create Restore Point", "red"))
                self.log_message(f"An unexpected error occurred while creating restore point: {e}", "ERROR")

        threading.Thread(target=_worker, daemon=True).start()

    def clear_icon_cache(self):
        if not self.prompt_for_admin("Clear Icon Cache"):
            return
        if not messagebox.askyesno("Confirm", "This will restart Windows Explorer and may cause your desktop to flash. All open Explorer windows will be closed.\n\nContinue?"):
            return
            
        self.log_message("Clearing icon cache...")
        self.show_notification("Clearing Icon Cache...", COLORS["accent"])

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
                
                self.after(0, lambda: self.show_notification("Icon Cache Cleared", COLORS["success"]))
            except Exception as e:
                self.log_message(f"Failed to clear icon cache: {e}", "ERROR")
                self.after(0, lambda: self.show_notification("Error Clearing Icon Cache", "red"))
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
            self.show_notification("Recycle Bin Emptied", COLORS["success"])
        except Exception as e:
            self.log_message(f"Error emptying Recycle Bin: {e}", "ERROR")
            self.show_notification("Error Emptying Recycle Bin", "red")

    def clean_temp_files(self):
        """Deletes files and folders from the user's temporary directory."""
        if not self.prompt_for_admin("Temp File Cleaning"):
            return

        if not messagebox.askyesno("Confirm Clean", "This will permanently delete files from your temporary folder. Are you sure you want to continue?"):
            return

        temp_dir = Path(os.environ.get("TEMP", ""))
        if not temp_dir.exists():
            self.show_notification("Temp Directory Not Found", "red")
            return

        self.log_message("Starting temp file cleanup...")
        self.show_notification("Cleaning Temp Files...", COLORS["accent"])
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
            self.show_notification(msg, COLORS["success"])
        else:
            self.show_notification("Temp Folder Already Clean", COLORS["subtext"])

    def run_command(self, command, success_msg):
        """Runs a shell command, requires admin, and shows notification."""
        if not self.prompt_for_admin(f"'{' '.join(command)}'"):
            return
        try:
            subprocess.run(command, check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.log_message(f"Ran command: '{' '.join(command)}'", "SUCCESS")
            self.show_notification(success_msg, COLORS["success"])
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.log_message(f"Command failed: '{' '.join(command)}'. Error: {e}", "ERROR")
            self.show_notification(f"Error: {e}", "red")

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
            self.show_notification(f"Prefetch cleared ({deleted} items)", COLORS["success"])
        except Exception as e:
            self.log_message(f"Prefetch clear failed: {e}", "ERROR")
            self.show_notification("Prefetch clear failed", "red")

    def reset_winsock(self):
        self.run_command(["netsh", "winsock", "reset"], "Winsock Reset Successful. Please Reboot.")

    def release_renew_ip(self):
        """Releases and renews the IP address for all adapters."""
        if not self.prompt_for_admin("IP Release/Renew"):
            return
        try:
            self.show_notification("Releasing IP Address...", COLORS["accent"])
            self.update_idletasks()
            subprocess.run(["ipconfig", "/release"], check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.log_message("IP Address Released.", "SUCCESS")
            
            self.show_notification("Renewing IP Address...", COLORS["accent"])
            self.update_idletasks()
            time.sleep(1) # Give adapters a moment
            subprocess.run(["ipconfig", "/renew"], check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.log_message("IP Address Renewed.", "SUCCESS")
            self.show_notification("IP Release/Renew Successful", COLORS["success"])
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.log_message(f"IP command failed: {e}", "ERROR")
            self.show_notification(f"Error: {e}", "red")

    def run_sfc_scan(self):
        """Runs sfc /scannow in a new administrative command prompt."""
        if not self.prompt_for_admin("System File Checker"):
            return
        
        if not messagebox.askyesno("Confirm SFC Scan", "This will scan and attempt to repair system files. This process can take a long time and cannot be cancelled easily.\n\nAre you sure you want to start?"):
            return

        try:
            self.log_message("Starting SFC /scannow in a new window.")
            self.show_notification("Starting SFC scan...", COLORS["accent"])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", "/k sfc /scannow", None, 1)
        except Exception as e:
            self.log_message(f"Failed to start SFC scan: {e}", "ERROR")
            self.show_notification("Failed to start SFC scan", "red")

    def run_dism_scan(self):
        """Runs DISM restore health."""
        if not self.prompt_for_admin("DISM Repair"): return
        if not messagebox.askyesno("Confirm DISM", "This will run 'DISM /Online /Cleanup-Image /RestoreHealth'.\nIt may take 10-20 minutes. Continue?"): return
        
        self.log_message("Starting DISM repair...")
        self.show_notification("Starting DISM Repair...", COLORS["accent"])
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", "/k dism /online /cleanup-image /restorehealth", None, 1)
        except Exception as e:
            self.show_notification("Failed to start DISM", "red")

    def clear_update_cache(self):
        """Clears Windows Update cache."""
        if not self.prompt_for_admin("Clear Update Cache"): return
        if not messagebox.askyesno("Confirm", "This will stop update services and clear the SoftwareDistribution folder. Continue?"): return

        self.show_notification("Clearing Update Cache...", COLORS["accent"])
        def _worker():
            try:
                subprocess.run("net stop wuauserv", shell=True)
                subprocess.run("net stop bits", shell=True)
                shutil.rmtree(r"C:\Windows\SoftwareDistribution", ignore_errors=True)
                subprocess.run("net start wuauserv", shell=True)
                subprocess.run("net start bits", shell=True)
                self.after(0, lambda: self.show_notification("Update Cache Cleared", COLORS["success"]))
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
                self.after(0, lambda: self.show_notification("Failed to get BitLocker keys", "red"))
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
                self.after(0, lambda: self.show_notification("Failed to fetch IP", "red"))
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
                self.after(0, lambda: self.show_notification("Error retrieving WiFi data", "red"))
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
                self.show_notification("Delivery Optimization cache cleared", COLORS["success"])
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
        self.show_notification("Error report cache cleared", COLORS["success"] if deleted else COLORS["subtext"])

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
        self.show_notification("Browser cache clear attempted", COLORS["success"])

    def network_reset_full(self):
        """Open Network status so user can run full Windows network reset (removes/reinstalls adapters; reboot required)."""
        self.open_shell_command("start ms-settings:network-status")
        self.log_message("Opened Network status. Use 'Network reset' for full reset (reboot required).")
        self.show_notification("Use 'Network reset' on the page for full reset", COLORS["accent"])

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

    def _scan_finish(self, root_size=None):
        """Called when worker has finished; apply size-based colors then hide progress."""
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
        """Single-threaded scan; stream results to tree in batches so UI updates as we go."""
        update_counter = [0]
        batch = []
        BATCH_SIZE = 50

        def flush_batch():
            if batch:
                self.after(0, self._insert_scan_batch, batch[:])
                batch.clear()

        def _build_tree(path):
            total_size = 0
            children = []
            try:
                for entry in os.scandir(path):
                    update_counter[0] += 1
                    if update_counter[0] % 200 == 0:
                        self.after(0, lambda p=entry.path: self.scan_status_label.configure(text=f"Scanning: {p[:70]}..."))

                    if entry.is_dir(follow_symlinks=False):
                        child_node = _build_tree(entry.path)
                        if child_node["size"] > 0:
                            children.append(child_node)
                            total_size += child_node["size"]
                            batch.append((path, child_node))
                            if len(batch) >= BATCH_SIZE:
                                flush_batch()
                    elif entry.is_file(follow_symlinks=False):
                        try:
                            file_size = entry.stat().st_size
                            total_size += file_size
                            if file_size > 1024 * 1024:
                                children.append({"name": entry.name, "path": entry.path, "size": file_size, "type": "file"})
                        except FileNotFoundError:
                            pass
            except (PermissionError, FileNotFoundError):
                pass
            return {"name": os.path.basename(path) or path, "path": path, "size": total_size, "type": "folder", "children": children}

        try:
            tree_data = _build_tree(root_path)
            flush_batch()
            self.after(0, self._scan_finish, tree_data["size"])
        except Exception as e:
            self.log_message(f"Disk scan failed: {e}", "ERROR")
            self.after(0, self.on_scan_complete, "Scan Failed!")

    def _populate_treeview(self, root_node):
        self.log_message("Scan complete. Populating view...")
        self.scan_status_label.configure(text="Populating view...")

        # Clear tree just in case
        for i in self.tree.get_children():
            self.tree.delete(i)

        def _format_size(size_bytes):
            if size_bytes == 0:
                return "0 B"
            size_name = ("B", "KB", "MB", "GB", "TB")
            i = int(math.floor(math.log(size_bytes, 1024))) if size_bytes > 0 else 0
            p = math.pow(1024, i)
            s = round(size_bytes / p, 2)
            return f"{s} {size_name[i]}"

        def _get_size_tag(item_size, root_size):
            if root_size == 0: return ''
            percentage = item_size / root_size
            if percentage > 0.15: return 'critical' # > 15%
            if percentage > 0.05: return 'high'     # > 5%
            if percentage > 0.01: return 'medium'   # > 1%
            return ''

        def _insert_node(parent_id, node, root_size):
            # Sort children by size, descending
            sorted_children = sorted(node.get('children', []), key=lambda x: x['size'], reverse=True)
            
            for child in sorted_children:
                tag = _get_size_tag(child['size'], root_size)
                icon = "📁" if child['type'] == 'folder' else "📄"

                node_id = self.tree.insert(parent_id, 'end', text=f" {icon} {child['name']}", 
                                           values=(_format_size(child['size']), child['path']),
                                           open=(child['size'] > root_size * 0.1), # Auto-open large folders
                                           tags=(tag,) if tag else ())
                if child['type'] == 'folder':
                    _insert_node(node_id, child, root_size)

        # Insert the root node's children
        _insert_node('', root_node, root_node['size'])
        
        self.on_scan_complete("Scan Complete.")

    def on_scan_complete(self, status_text):
        try:
            self.scan_progress_bar.stop()
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
            self.show_notification("Error opening location", "red")

    def _tree_delete_item(self):
        if not self.tree.selection():
            return
        selected_id = self.tree.selection()[0]
        path_str = self.tree.item(selected_id, 'values')[1]
        
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to move this item to the Recycle Bin?\n\n{path_str}"):
            return

        if send_to_recycle_bin(str(path_str)):
            self.log_message(f"Moved to Recycle Bin: {path_str}", "SUCCESS")
            self.show_notification("Item moved to Recycle Bin", COLORS["success"])
            # Remove from treeview
            self.tree.delete(selected_id)
            if hasattr(self, "scanner_empty_label") and not self.tree.get_children():
                self.scanner_empty_label.place(relx=0.5, rely=0.5, anchor="center")
            # Note: Parent sizes will not be updated. A rescan is needed for accuracy.
            self.scan_status_label.configure(text="Item deleted. Sizes may be inaccurate until next scan.")
        else:
            self.log_message(f"Failed to move to Recycle Bin: {path_str}", "ERROR")
            self.show_notification("Failed to delete item", "red")

    def open_sys_tool(self, tool):
        try:
            subprocess.Popen(tool)
            self.log_message(f"Opened system tool: {tool}")
        except FileNotFoundError:
            self.log_message(f"Could not open {tool}", "ERROR")
            self.show_notification(f"Could not open {tool}", "red")

    def open_shell_command(self, command):
        """Executes a command using the shell, e.g., for 'start' commands."""
        try:
            subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.log_message(f"Executed shell command: {command}")
        except Exception as e:
            self.log_message(f"Could not execute {command}: {e}", "ERROR")
            self.show_notification(f"Could not execute {command}", "red")

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
            self.show_notification(f"{friendly_name} is already clean", COLORS["subtext"])
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
            self.show_notification(f"Cleaned {len(sorted_files)} Items from {friendly_name}", COLORS["success"])
        elif not error_files:
            self.show_notification(f"{friendly_name} is already clean", COLORS["subtext"])

    def perform_sort(self):
        """Wrapper to clean the Desktop folder."""
        self._perform_folder_sort(DESKTOP_PATH, "Desktop_Cleanup", "Desktop")

    def perform_downloads_sort(self):
        """Wrapper to clean the Downloads folder."""
        self._perform_folder_sort(DOWNLOADS_PATH, "Downloads_Cleanup", "Downloads Folder")

    def load_config(self):
        default_rules = {
            "Visuals": [".jpg", ".png", ".webp", ".jpeg", ".gif", ".svg", ".heic"],
            "Videos": [".mp4", ".mov", ".avi", ".mkv"],
            "Audio": [".mp3", ".wav", ".flac", ".aac"],
            "Docs": [".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".md"],
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "Dev": [".py", ".ps1", ".js", ".html", ".css", ".json", ".xml", ".ipynb"],
            "Installers": [".exe", ".msi"]
        }
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.rules = config.get("sorting_rules", default_rules)
            except (json.JSONDecodeError, IOError):
                self.rules = default_rules
                self.save_config()
        else:
            self.rules = default_rules
            self.save_config()

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({"sorting_rules": self.rules}, f, indent=4)
        except IOError as e:
            self.show_notification(f"Error saving config: {e}", "red")

if __name__ == "__main__":
    app = OmbraApp()
    app.mainloop()