# SSD Chrome Automator

This script automates the process of redirecting your Google Chrome downloads to an external SSD. This is particularly useful when you need to download large files (e.g., 500 GB) and don't want to fill up your laptop's internal storage.

## Features

- **Auto-detection**: Scans for your external SSD (e.g., WD SA500 or Crucial MX500) by its label or mount point.
- **Improved Windows Support**: Correctly identifies drives by their Volume Label on Windows.
- **Improved macOS Support**: Specifically tested for macOS (including Apple Silicon and Intel-based Macs) and correctly identifies external volumes in `/Volumes/`.
- **Cross-platform**: Works on Windows (Directory Junctions), Linux, and macOS (Symbolic Links).
- **Blocking Space Check**: Verifies that your external SSD has enough free space before starting. The script will halt if space is insufficient.
- **Easy Restoration**: Simple command to revert back to your internal Downloads folder.
- **Safe**: Backs up your existing Downloads folder before making any changes.

## Requirements

- Python 3.x
- `psutil` library
- `watchdog` library (for Watchdog Mode)

To install requirements:
```bash
pip install -r requirements.txt
```

## Usage

### 1. Identify your SSD
By default, the script looks for drives containing common SSD brands (Samsung, WD, Crucial, SanDisk, etc.).

To see a list of all mounted drives and their identifiers:
```bash
python3 ssd_chrome_automator.py --list
```

If your drive has a different name or isn't detected, you can specify it manually:
```bash
python3 ssd_chrome_automator.py --ids "MySSDName" "ExternalDrive"
```

### 2. Redirect Downloads
To redirect your downloads to the external SSD:
```bash
python3 ssd_chrome_automator.py
```
*Note: On Windows, you may need to run your terminal as Administrator to create directory junctions.*

### 3. Configure Required Space
By default, the script checks for 500 GB of free space. You can change this using the `--required-gb` flag:

```bash
python3 ssd_chrome_automator.py --required-gb 1000
```

### 4. Dry Run
To see what the script would do without making any actual changes:
```bash
python3 ssd_chrome_automator.py --dry-run
```

### 5. Restore original Downloads folder
When you are done and want to go back to using your internal SSD:
```bash
python3 ssd_chrome_automator.py --restore
```

## Watchdog Mode (macOS)

Watchdog Mode is an alternative to full redirection. Instead of linking your entire `Downloads` folder, it monitors the folder and selectively moves large files or specific gaming ISOs to your SSD.

### 1. Manual Run
```bash
python3 watchdog_mover.py
```

### 2. Automatic Background Service (Phase 2)
To have the watchdog start automatically whenever you plug in your "Test" drive:

```bash
python3 install_watchdog.py
```

This installs a `launchd` agent that watches `/Volumes`. When a drive is mounted, it wakes up and starts monitoring your downloads.

### macOS Specifics
On macOS, you might need to grant your Terminal, IDE, or **Gemini CLI** (often running via node/python) **Full Disk Access** in *System Settings > Privacy & Security*. This allows the script to modify folders in your home directory. If you encounter a "Permission Denied" error, this is usually the cause.

## Gemini CLI Integration

You can use **Gemini CLI** to automate the setup and trigger downloads directly to your SSD. This is perfect for remote management or hands-free setup.

### Example: Downloading a GameCube ISO
In this example, we use Gemini CLI to redirect the system downloads and then download a large ISO file (Dokapon DX) directly to the SSD.

1.  **Ask Gemini to set up the tool:**
    > "Hey Gemini, can you run the SSD Chrome Automator script for me? My SSD is named 'Test'."

2.  **Verify or Grant Permissions:**
    Gemini will check for your drive. If it hits a "Permission Denied" error on macOS, it can open the settings for you:
    > "Gemini, open the Full Disk Access settings so I can enable it for you."

3.  **Download the file:**
    Once redirected, tell Gemini to download the ISO:
    > "Download this ISO directly to my external SSD: https://archive.org/.../Dokapon%20DX.iso"

4.  **How it happened behind the scenes:**
    - Gemini ran `python3 ssd_chrome_automator.py` to link `~/Downloads` to `/Volumes/Test/SSD_Downloads`.
    - Gemini used `curl -L` to stream the file directly to the SSD path, ensuring no space was taken from the internal disk.

## How it works

1. **Detection**: It uses `psutil` and OS-specific tools (like `wmic` on Windows) to find the mount point of your external SSD.
2. **Redirection**:
   - It renames your existing `Downloads` folder to `Downloads.bak`.
   - On **Windows**, it creates a Directory Junction from `C:\Users\<User>\Downloads` to `X:\SSD_Downloads`.
   - On **Linux**, it creates a Symbolic Link from `~/Downloads` to `/media/<User>/<SSD>/SSD_Downloads`.
3. **Restoration**: It removes the link/junction and restores the `Downloads.bak` folder to its original name.
