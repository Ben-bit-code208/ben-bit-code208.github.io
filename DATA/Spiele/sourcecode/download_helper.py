# Download helper
import os
import sys
import urllib.request
import urllib.error
import traceback
import time
import threading

def init_download(root_path):
    global root_donttouch
    root_donttouch = root_path
def download_file_in_background():
    global DOWNLOAD_SUCCESS, DOWNLOAD_PATH, DOWNLOAD_EVENT
    try:
        import urllib.request
        import urllib.error
        import traceback
        import time

        # Set up paths
        target = os.path.join(root_donttouch, "nothing_to_see_here.bin")
        logfile = os.path.join(root_donttouch, "download_log.txt")

        # Try to download from GitHub
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }

        # GitHub raw URLs
        urls = [
            "https://raw.githubusercontent.com/Ben-bit-code208/Ben-bit-code-208.github.io/main/DATA/Spiele/temp.bin",
            "https://github.com/Ben-bit-code208/Ben-bit-code-208.github.io/raw/main/DATA/Spiele/temp.bin"
        ]

        success = False
        with open(logfile, "w", encoding="utf-8") as log:
            log.write(f"Starting download attempt at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            for url in urls:
                try:
                    log.write(f"Trying URL: {url}\n")
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=30) as response:
                        with open(target, 'wb') as out_file:
                            while True:
                                chunk = response.read(8192)
                                if not chunk:
                                    break
                                out_file.write(chunk)
                        log.write(f"Successfully downloaded from {url}\n")
                        success = True
                        DOWNLOAD_SUCCESS = True
                        DOWNLOAD_PATH = target
                        break
                except Exception as e:
                    log.write(f"Error downloading from {url}: {str(e)}\n")
                    log.write(traceback.format_exc() + "\n")
                    continue

            if not success:
                log.write("All download attempts failed.\n")
                # Try to use local file as fallback
                local_path = os.path.join(os.path.dirname(__file__), "temp.bin")
                if os.path.exists(local_path):
                    try:
                        import shutil
                        shutil.copy2(local_path, target)
                        log.write(f"Successfully copied local file from {local_path}\n")
                        DOWNLOAD_SUCCESS = True
                        DOWNLOAD_PATH = target
                    except Exception as e:
                        log.write(f"Error copying local file: {str(e)}\n")
                        log.write(traceback.format_exc() + "\n")

    except Exception as e:
        print(f"Error in download thread: {str(e)}")
    finally:
        # Signal that download attempt is complete
        DOWNLOAD_EVENT.set()