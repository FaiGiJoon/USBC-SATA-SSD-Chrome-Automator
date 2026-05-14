import os
import sys
import subprocess
import platform

def install():
    if platform.system() != "Darwin":
        print("Error: This installation script is designed for macOS (launchd).")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    watchdog_script = os.path.join(script_dir, "watchdog_mover.py")
    template_path = os.path.join(script_dir, "com.casper.ssd.automator.plist.template")

    if not os.path.exists(template_path):
        print(f"Error: Template not found at {template_path}")
        return

    # 1. Read template
    with open(template_path, 'r') as f:
        template_content = f.read()

    # 2. Fill template with absolute paths
    python_path = sys.executable
    plist_content = template_content.format(
        python_path=python_path,
        script_path=watchdog_script
    )

    # 3. Write to LaunchAgents
    launch_agents_dir = os.path.expanduser("~/Library/LaunchAgents")
    os.makedirs(launch_agents_dir, exist_ok=True)

    plist_filename = "com.casper.ssd.automator.plist"
    dest_path = os.path.join(launch_agents_dir, plist_filename)

    print(f"Writing plist to {dest_path}...")
    with open(dest_path, 'w') as f:
        f.write(plist_content)

    # 4. Load the service
    print("Loading service with launchctl...")
    try:
        # Unload first if already loaded
        subprocess.run(["launchctl", "unload", dest_path], capture_output=True)
        subprocess.run(["launchctl", "load", dest_path], check=True)
        print("Watchdog service successfully installed and loaded!")
        print("Logs can be found in /tmp/com.casper.ssd.automator.std*.log")
    except subprocess.CalledProcessError as e:
        print(f"Error loading service: {e}")

if __name__ == "__main__":
    install()
