import urllib.request
import urllib.error
import concurrent.futures
import socket
import contextlib

# Reduziere den globalen Socket-Timeout
socket.setdefaulttimeout(5)

urls = [
    "https://github.com/Ben-bit-code208/game-data/raw/main/temp.bin",  # Korrigierte URL
    "https://raw.githubusercontent.com/Ben-bit-code208/game-data/main/temp.bin"
]

headers = {'User-Agent': 'Mozilla/5.0'}

def check_url(url):
    try:
        req = urllib.request.Request(url, headers=headers, method='HEAD')
        with contextlib.closing(urllib.request.urlopen(req, timeout=5)) as resp:
            status = resp.status
            return (url, 'OK', status)
    except urllib.error.HTTPError as he:
        return (url, 'HTTPError', f"{he.code} {he.reason}")
    except urllib.error.URLError as ue:
        return (url, 'URLError', str(ue.reason))
    except Exception as e:
        return (url, 'ERROR', str(e))

# Parallele URL-Überprüfung mit Timeout
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    # Starte alle URLs parallel
    future_to_url = {executor.submit(check_url, url): url for url in urls}
    
    # Sammle Ergebnisse mit Timeout
    for future in concurrent.futures.as_completed(future_to_url, timeout=10):
        url = future_to_url[future]
        try:
            url, status, details = future.result()
            print(f"{url} -> {status}: {details}")
        except concurrent.futures.TimeoutError:
            print(f"{url} -> TIMEOUT: Operation took too long")
        except Exception as e:
            print(f"{url} -> FAILED: {str(e)}")
