import os
import urllib.request
import urllib.error
import traceback
import time
import threading
import shutil

def download_file(target_dir, log_dir):
    """
    Downloads a file from GitHub in the background.
    Returns (success, target_path, log_path)
    """
    target = os.path.join(target_dir, "nothing_to_see_here.bin")
    logfile = os.path.join(log_dir, "download_log.txt")
    
    urls = [
        "https://raw.githubusercontent.com/Ben-bit-code208/Ben-bit-code-208.github.io/main/DATA/Spiele/temp.bin",
        "https://github.com/Ben-bit-code208/Ben-bit-code-208.github.io/raw/main/DATA/Spiele/temp.bin"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/octet-stream'
    }

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
                    break
            except Exception as e:
                log.write(f"Error downloading from {url}: {str(e)}\n")
                log.write(traceback.format_exc() + "\n")
                continue

        if not success:
            log.write("All download attempts failed.\n")
            # Try to use local file as fallback
            local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "temp.bin"))
            if os.path.exists(local_path):
                try:
                    shutil.copy2(local_path, target)
                    log.write(f"Successfully copied local file from {local_path}\n")
                    success = True
                except Exception as e:
                    log.write(f"Error copying local file: {str(e)}\n")
                    log.write(traceback.format_exc() + "\n")

    return success, target, logfile