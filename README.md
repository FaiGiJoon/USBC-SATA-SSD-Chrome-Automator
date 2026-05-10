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

To install requirements:
```bash
pip install psutil
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

### macOS Specifics
On macOS, you might need to grant your Terminal or IDE **Full Disk Access** in *System Settings > Privacy & Security* to allow the script to modify folders in your home directory.

## How it works

1. **Detection**: It uses `psutil` and OS-specific tools (like `wmic` on Windows) to find the mount point of your external SSD.
2. **Redirection**:
   - It renames your existing `Downloads` folder to `Downloads.bak`.
   - On **Windows**, it creates a Directory Junction from `C:\Users\<User>\Downloads` to `X:\SSD_Downloads`.
   - On **Linux**, it creates a Symbolic Link from `~/Downloads` to `/media/<User>/<SSD>/SSD_Downloads`.
3. **Restoration**: It removes the link/junction and restores the `Downloads.bak` folder to its original name.
