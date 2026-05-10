#!/usr/bin/env python3
import os
import sys
import platform
import shutil
import json
import subprocess

# Handle dependency check for psutil
try:
    import psutil
except ImportError:
    print("Error: The 'psutil' library is not installed.")
    print("Please install it using: pip install psutil")
    sys.exit(1)

import argparse

def get_windows_volume_label(drive_letter):
    """
    Returns the volume label for a given drive letter on Windows.
    """
    try:
        # Use wmic to get the VolumeName for the specified drive
        cmd = f'wmic logicaldisk where name="{drive_letter}" get volumename'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            return lines[1].strip()
    except Exception:
        pass
    return ""

def list_drives():
    """
    Lists all mounted drives and their details.
    """
    print(f"{'Device':<20} {'Mount Point':<30} {'Label/Name':<20}")
    print("-" * 75)
    partitions = psutil.disk_partitions(all=False)
    for p in partitions:
        label = ""
        if platform.system() == "Windows":
            label = get_windows_volume_label(p.mountpoint.strip('\\'))

        print(f"{p.device:<20} {p.mountpoint:<30} {label:<20}")

def find_target_ssd(identifiers):
    """
    Scans mounted partitions to find the target SSD based on provided identifiers (labels or mount points).
    """
    # On macOS and Linux, all=False should give us what we need.
    partitions = psutil.disk_partitions(all=False)
    for p in partitions:
        # Check mountpoint and device name (covers Linux/macOS)
        for ident in identifiers:
            if ident.lower() in p.mountpoint.lower() or ident.lower() in p.device.lower():
                # Basic check to avoid system root if searching for generic terms
                if p.mountpoint == '/' and 'external' not in ident.lower():
                    continue
                return p.mountpoint
        
        # On Windows, check the volume label
        if platform.system() == "Windows":
            label = get_windows_volume_label(p.mountpoint.strip('\\'))
            for ident in identifiers:
                if ident.lower() in label.lower():
                    return p.mountpoint
                    
    return None

def get_chrome_downloads_path():
    """
    Returns the standard Chrome Downloads path for the current OS.
    """
    home = os.path.expanduser("~")
    # Standard Downloads folder is usually the same path across major OSes relative to home
    return os.path.join(home, "Downloads")

def check_chrome_running():
    """
    Checks if Google Chrome is currently running and warns the user.
    """
    chrome_names = ["chrome", "google chrome", "google-chrome"]
    running = False
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info['name'].lower()
            if any(chrome_name in name for chrome_name in chrome_names):
                running = True
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    if running:
        print("WARNING: Google Chrome appears to be running.")
        print("It is recommended to close Chrome before redirecting or restoring the Downloads folder.")
        # We don't force exit, just warn.

def is_junction(path):
    if platform.system() != "Windows":
        return False
    if not os.path.exists(path):
        return False
    # Use attrib to check for 'L' (Reparse Point) attribute
    try:
        result = subprocess.run(['attrib', path], capture_output=True, text=True)
        return 'L' in result.stdout.split()
    except Exception:
        return False

def redirect_downloads(ssd_path, required_gb, target_dir_name="SSD_Downloads"):
    """
    Redirects the system Downloads folder to the external SSD using a symlink or junction.
    """
    # 1. Check Space First (Blocking)
    if not check_space(ssd_path, required_gb):
        print("Error: Insufficient space on target SSD. Aborting redirection.")
        sys.exit(1)

    # 2. Check if target SSD is writable
    if not os.access(ssd_path, os.W_OK):
        print(f"Error: Target SSD at {ssd_path} is not writable. Please check permissions.")
        sys.exit(1)

    ssd_downloads = os.path.join(ssd_path, target_dir_name)
    try:
        if not os.path.exists(ssd_downloads):
            os.makedirs(ssd_downloads)
            print(f"Created directory: {ssd_downloads}")
    except OSError as e:
        print(f"Error creating directory on SSD: {e}")
        sys.exit(1)

    local_downloads = get_chrome_downloads_path()
    backup_path = local_downloads + ".bak"

    # Check if already redirected
    if os.path.islink(local_downloads) or is_junction(local_downloads):
        print(f"Downloads folder is already a link or junction. Skipping redirection.")
        return

    # Move existing Downloads to backup
    if os.path.exists(local_downloads):
        if os.path.exists(backup_path):
             print(f"Error: Backup already exists at {backup_path}. Please handle manually.")
             sys.exit(1)
        
        print(f"Moving local Downloads to {backup_path}...")
        try:
            os.rename(local_downloads, backup_path)
        except OSError as e:
            print(f"Error backing up Downloads folder: {e}")
            sys.exit(1)

    # Create link
    print(f"Linking {local_downloads} -> {ssd_downloads}...")
    try:
        if platform.system() == "Windows":
            # Using directory junction for better compatibility on Windows
            subprocess.run(['mklink', '/J', local_downloads, ssd_downloads], shell=True, check=True)
        else:
            os.symlink(ssd_downloads, local_downloads)
        print("Redirection successful!")
    except (subprocess.CalledProcessError, OSError) as e:
        print(f"Error creating link: {e}")
        # Try to restore backup if we failed
        if os.path.exists(backup_path) and not os.path.exists(local_downloads):
            print("Attempting to restore original Downloads folder...")
            os.rename(backup_path, local_downloads)
        sys.exit(1)

def check_space(path, required_gb):
    """
    Checks if the given path has at least required_gb of free space.
    """
    try:
        usage = psutil.disk_usage(path)
        free_gb = usage.free / (1024**3)
        print(f"Available space on {path}: {free_gb:.2f} GB")
        if free_gb < required_gb:
            print(f"WARNING: Less than {required_gb} GB available!")
            return False
        return True
    except Exception as e:
        print(f"Error checking space: {e}")
        return False

def restore_downloads():
    """
    Restores the original Downloads folder by removing the symlink/junction and restoring the backup.
    """
    local_downloads = get_chrome_downloads_path()
    backup_path = local_downloads + ".bak"

    if os.path.islink(local_downloads) or is_junction(local_downloads):
        print(f"Removing link/junction: {local_downloads}")
        try:
            if platform.system() == "Windows":
                 # rmdir on a junction only removes the junction, not the target content
                 subprocess.run(['rmdir', local_downloads], shell=True, check=True)
            else:
                 os.remove(local_downloads)
        except (subprocess.CalledProcessError, OSError) as e:
            print(f"Error removing link: {e}")
            return

    if os.path.exists(backup_path):
        print(f"Restoring backup from {backup_path}...")
        try:
            os.rename(backup_path, local_downloads)
            print("Restoration successful!")
        except OSError as e:
            print(f"Error restoring backup: {e}")
    else:
        print("No backup found to restore. Creating empty Downloads folder.")
        os.makedirs(local_downloads, exist_ok=True)

def main():
    parser = argparse.ArgumentParser(description="Automate Chrome downloads to an external SSD.")
    default_ids = [
        'WD SA500', 'Crucial MX500', 'Samsung', 'SanDisk',
        'Seagate', 'Toshiba', 'Pioneer', 'LaCie', 'External'
    ]
    parser.add_argument('--ids', nargs='+', default=default_ids,
                        help='Identifiers for the external SSD (labels or parts of the mount path).')
    parser.add_argument('--list', action='store_true', help='List all mounted drives.')
    parser.add_argument('--restore', action='store_true', help='Restore the original Downloads folder.')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making changes.')
    parser.add_argument('--required-gb', type=int, default=500, help='Required free space in GB (default: 500).')
    
    args = parser.parse_args()

    if args.list:
        list_drives()
        return
    
    if args.restore:
        if args.dry_run:
            print("[DRY-RUN] Would restore original Downloads folder.")
        else:
            restore_downloads()
        return

    print(f"Searching for external SSD with identifiers: {args.ids}...")
    ssd_path = find_target_ssd(args.ids)

    # Check for Chrome running
    check_chrome_running()
    
    if ssd_path:
        print(f"Found target SSD at: {ssd_path}")
        if args.dry_run:
            print(f"[DRY-RUN] Checking for {args.required_gb} GB free space.")
            check_space(ssd_path, args.required_gb)
            print(f"[DRY-RUN] Would redirect Downloads to {ssd_path}/SSD_Downloads")
        else:
            redirect_downloads(ssd_path, args.required_gb)
    else:
        print("Target SSD not found. Please ensure it is plugged in and mounted.")

if __name__ == "__main__":
    main()
