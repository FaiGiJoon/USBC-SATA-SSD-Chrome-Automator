import os
import time
import shutil
import logging
import argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import ssd_chrome_automator

# Configuration
LARGE_FILE_THRESHOLD_MB = 500
TARGET_EXTENSIONS = {'.iso', '.rvz', '.nds'}
DEFAULT_SSD_IDENTIFIERS = ['Test', 'WD SA500', 'Crucial MX500', 'Samsung', 'SanDisk', 'External']

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('WatchdogMover')

class DownloadHandler(FileSystemEventHandler):
    def __init__(self, ssd_identifiers, target_dir_name="SSD_Downloads"):
        self.ssd_identifiers = ssd_identifiers
        self.target_dir_name = target_dir_name

    def on_created(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.process_file(event.dest_path)

    def process_file(self, file_path):
        filename = os.path.basename(file_path)
        _, extension = os.path.splitext(filename)

        # Skip temporary download files
        if extension.lower() in ['.crdownload', '.tmp', '.part', '.download']:
            return

        # Wait briefly for file to be released (especially important for browsers)
        time.sleep(2)

        if not os.path.exists(file_path):
            return

        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > LARGE_FILE_THRESHOLD_MB or extension.lower() in TARGET_EXTENSIONS:

                # Locate SSD at the moment of move to handle dynamic mounting
                ssd_path = ssd_chrome_automator.find_target_ssd(self.ssd_identifiers)
                if not ssd_path:
                    logger.warning(f"Detected {filename} but target SSD not found. Skipping move.")
                    return

                target_dir = os.path.join(ssd_path, self.target_dir_name)
                os.makedirs(target_dir, exist_ok=True)

                logger.info(f"Moving {filename} ({file_size_mb:.2f} MB) to SSD...")
                dest_path = os.path.join(target_dir, filename)

                # Handle filename collisions
                if os.path.exists(dest_path):
                    base, ext = os.path.splitext(filename)
                    dest_path = os.path.join(target_dir, f"{base}_{int(time.time())}{ext}")

                shutil.move(file_path, dest_path)
                logger.info(f"Successfully moved to {dest_path}")
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")

def initial_scan(downloads_path, handler):
    """Scan existing files in the downloads folder."""
    logger.info("Performing initial scan of downloads directory...")
    for filename in os.listdir(downloads_path):
        file_path = os.path.join(downloads_path, filename)
        if os.path.isfile(file_path):
            handler.process_file(file_path)

def main():
    parser = argparse.ArgumentParser(description="Watchdog to move large downloads to SSD.")
    parser.add_argument('--ids', nargs='+', default=DEFAULT_SSD_IDENTIFIERS,
                        help='Identifiers for the external SSD.')
    parser.add_argument('--no-scan', action='store_true', help='Skip initial scan of Downloads folder.')
    args = parser.parse_args()

    downloads_path = ssd_chrome_automator.get_chrome_downloads_path()
    logger.info(f"Monitoring {downloads_path}...")
    logger.info(f"Target SSD Identifiers: {args.ids}")

    event_handler = DownloadHandler(args.ids)

    if not args.no_scan:
        initial_scan(downloads_path, event_handler)

    observer = Observer()
    observer.schedule(event_handler, downloads_path, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
