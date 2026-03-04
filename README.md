# ombra

A clean collection of **fast, private, ad‑free** tools: a website of in-browser utilities and **Ombra Utility Pro**, a Windows desktop app for cleanup, system info, and service desk tasks.

**Repo:** [undrwtrsprite/ombra.cc](https://github.com/undrwtrsprite/ombra.cc)

---

## 🖥️ Ombra Utility Pro (Windows desktop app)

A privacy-first Windows tool for quick cleanup, system info, installers, and file scanning. No telemetry, no accounts—everything runs on your machine. Built for service desk, power users, and anyone who wants control without bloat.

### Download

- **Latest release:** [Download OmbraUtilityPro.exe](https://github.com/undrwtrsprite/ombra.cc/releases/latest/download/OmbraUtilityPro.exe)
- **All releases:** [Releases](https://github.com/undrwtrsprite/ombra.cc/releases)

Runs on Windows 10/11. No install required—run the exe directly.

### Features

- **Cleanup:** Temp files, thumbnail cache, recycle bin, DNS flush, Desktop/Downloads sorting
- **System:** CPU/RAM graph, storage scanner, system & hardware info, M365 credential reset
- **Installer:** Browse and install apps (winget-style)
- **File scanner:** Find large files by drive
- **Logs:** Built-in activity log

### Build from source

```bash
cd ombrautil
pip install -r requirements.txt
pip install pyinstaller
# Optional: python create_icon.py   # regenerate icon.ico with multiple sizes
pyinstaller OmbraUtility.spec
# Output: ombrautil/dist/Ombra Utility Pro.exe
```

### Release workflow

Pushing a version tag builds the exe and publishes it to GitHub Releases:

```bash
git tag v1.0.0
git push origin v1.0.0
```

The [Release Ombra Utility Pro](.github/workflows/release-utility.yml) workflow runs on tag push `v*`, builds the executable, and uploads `OmbraUtilityPro.exe` to the release.

---

## 🌐 ombra tools (website)

A privacy-first collection of in-browser tools. No data leaves your device.

### ✨ Features

- **🔒 100% Private**: All processing happens locally in your browser
- **📱 Works Offline**: Service worker caches everything for offline use
- **🚀 PWA Ready**: Install as a native app on mobile/desktop
- **🎨 Beautiful Design**: Glass-morphism UI with smooth animations
- **⚡ Fast**: No server round-trips, instant results
- **📱 Responsive**: Works on all devices

### 🛡️ Privacy & Security

- **No Uploads**: Files never leave your device
- **No Tracking**: Zero analytics or user tracking
- **No Cookies**: Clean, stateless operation
- **Local Processing**: All tools run in your browser
- **Offline First**: Works without internet connection

### 🛠️ Tools (browser)

**Images & PDFs** — Image Converter, Resizer, PDF to Text, Text to PDF, PDF Merger, Image to PDF, HEIC to JPG, File Compressor  

**Text & Data** — QR Code, Color Picker, Text Case, JSON Formatter, Markdown Editor, Notepad, Text Diff, JSON/CSV Converter  

**IT & Network** — IP Calculator, IP Info, WHOIS, DNS Lookup, Unix Time, UUID Generator  

**Utilities** — Ombra Utility Pro (desktop), QR Scanner, Unit Converter, Stopwatch, Currency Converter, Password Generator, and more  

### 🎯 Getting started

1. **Website:** Visit the site (e.g. [ombra.cc](https://ombra.cc) or your deployment)
2. **Desktop app:** [Download Ombra Utility Pro](https://github.com/undrwtrsprite/ombra.cc/releases/latest/download/OmbraUtilityPro.exe) for Windows
3. **PWA:** Use “Install” in the browser for the web app
4. **Offline:** All browser tools work without internet

### 🔧 Tech

- **Web:** Vanilla HTML/CSS/JavaScript, Service Worker, PWA manifest
- **Desktop app:** Python, CustomTkinter, PyInstaller (Windows)

---

Built with care and privacy in mind.  
**© 2025 ombra**
