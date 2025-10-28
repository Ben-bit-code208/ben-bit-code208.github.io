import sys
import threading
import time
import os
import subprocess
global _ping_rc


try:
    import tkinter as tk
    from tkinter import messagebox
except Exception:
    # Fallback for older Python (2.x) names using importlib so linters won't
    # report an unresolved import for the legacy module names.
    try:
        import importlib
        tk = importlib.import_module("Tkinter")
        messagebox = importlib.import_module("tkMessageBox")
    except Exception:
        print("Tkinter is required (usually included with Python).")
        sys.exit(1)

# gettinghacked.py
# Play a YouTube video fullscreen without UI (requires internet).
# Dependencies: yt_dlp (or youtube-dl fork) and python-vlc
# Install: pip install yt-dlp python-vlc


from yt_dlp import YoutubeDL
try:
    import importlib
    vlc = importlib.import_module("vlc")
except Exception as e:
    # Provide a clearer diagnostic when python-vlc can't load libvlc (common on Windows)
    print("python-vlc (import name 'vlc') is required. Install with: pip install python-vlc")
    print("ImportError details:", repr(e))
    print("On Windows this commonly means the VLC runtime (libvlc.dll) is not found.")
    print("Install VLC from https://www.videolan.org/ and ensure its installation folder (e.g. 'C:\\Program Files\\VideoLAN\\VLC') is on your PATH.")
    print("Also ensure Python and VLC architectures match (both 64-bit or both 32-bit).")
    sys.exit(1)

YOUTUBE_URL = "https://www.youtube.com/watch?app=desktop&v=P9NX0hqPMuI&t=8s"
import threading
import time
try:
    import tkinter as tk
    from tkinter import messagebox
except Exception:
    # Fallback for older Python (2.x) names using importlib so linters won't
    # report an unresolved import for the legacy module names.
    try:
        import importlib
        tk = importlib.import_module("Tkinter")
        messagebox = importlib.import_module("tkMessageBox")
    except Exception:
        print("Tkinter is required (usually included with Python).")
        sys.exit(1)

# gettinghacked.py
# Play a YouTube video fullscreen without UI (requires internet).
# Dependencies: yt_dlp (or youtube-dl fork) and python-vlc
# Install: pip install yt-dlp python-vlc


from yt_dlp import YoutubeDL
try:
    import importlib
    vlc = importlib.import_module("vlc")
except Exception as e:
    # Provide a clearer diagnostic when python-vlc can't load libvlc (common on Windows)
    print("python-vlc (import name 'vlc') is required. Install with: pip install python-vlc")
    print("ImportError details:", repr(e))
    print("On Windows this commonly means the VLC runtime (libvlc.dll) is not found.")
    print("Install VLC from https://www.videolan.org/ and ensure its installation folder (e.g. 'C:\\Program Files\\VideoLAN\\VLC') is on your PATH.")
    print("Also ensure Python and VLC architectures match (both 64-bit or both 32-bit).")
    sys.exit(1)

YOUTUBE_URL = "https://www.youtube.com/watch?app=desktop&v=P9NX0hqPMuI&t=8s"


def get_direct_stream(url):
    opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        # If 'url' present, it's a direct stream; otherwise pick best format entry
        if "url" in info and info["url"]:
            return info["url"]
        formats = info.get("formats") or []
        # Prefer combined mp4 or highest resolution progressive
        for f in sorted(formats, key=lambda x: (x.get("height") or 0), reverse=True):
            if f.get("ext", "").lower() in ("mp4", "m4v", "webm", "mkv") and f.get("acodec") != "none":
                return f.get("url")
        # fallback to last format url
        if formats:
            return formats[-1].get("url")
    return None


class FullscreenPlayer:
    def __init__(self, stream_url):
        self.stream_url = stream_url
        # Disable HW acceleration to avoid Direct3D11 issues on Windows
        # and use no-xlib which is harmless on other platforms
        try:
            self.instance = vlc.Instance("--no-xlib", "--avcodec-hw=none")
        except TypeError:
            # Older python-vlc may expect a single string or different constructor; fall back
            try:
                self.instance = vlc.Instance(["--no-xlib", "--avcodec-hw=none"])  # type: ignore
            except Exception:
                self.instance = vlc.Instance("--no-xlib")
        self.player = self.instance.media_player_new()
        self.root = tk.Tk()
        self.root.title("Cutscene")
        self.root.configure(bg="black")
        self.root.attributes("-fullscreen", True)
        self.root.config(cursor="none")
        self.root.bind("<Escape>", lambda e: self.close())
        self.root.bind("<Button-1>", lambda e: self.close())
        # Frame to embed video
        self.frame = tk.Frame(self.root, bg="black")
        self.frame.pack(fill=tk.BOTH, expand=1)
        # Delay setting the window handle until after Tk maps the frame to avoid HWND timing issues
        self.root.after(0, self._set_window_handle_after_map)
        # Stop app if VLC stops (end of stream)
        self.monitor_thread = threading.Thread(target=self._monitor_playback, daemon=True)

    def _set_window_handle_after_map(self):
        # Ensure window ID is available
        self.root.update_idletasks()
        hwnd = self.frame.winfo_id()
        if sys.platform.startswith("win"):
            try:
                # set_hwnd may raise on some builds; guard it
                self.player.set_hwnd(hwnd)
            except Exception:
                pass
        elif sys.platform.startswith("linux"):
            self.player.set_xwindow(hwnd)
        elif sys.platform == "darwin":
            # macOS: python-vlc may not support set_nsobject reliably; try set_nsobject if present
            try:
                self.player.set_nsobject(hwnd)
            except Exception:
                pass

    def play(self):
        media = self.instance.media_new(self.stream_url)
        self.player.set_media(media)
        self.player.play()
        # Attach VLC event callbacks to close the tkinter window when playback ends/errors/stops
        try:
            em = self.player.event_manager()
            # VLC event callbacks run in VLC thread; use root.after to schedule tkinter-safe close
            em.event_attach(vlc.EventType.MediaPlayerEndReached, lambda e: self.root.after(0, self.close))
            em.event_attach(vlc.EventType.MediaPlayerEncounteredError, lambda e: self.root.after(0, self.close))
            em.event_attach(vlc.EventType.MediaPlayerStopped, lambda e: self.root.after(0, self.close))
        except Exception:
            # If attaching events fails for any reason, continue with the monitor thread fallback
            pass
        self.monitor_thread.start()
        self.root.mainloop()

    def _monitor_playback(self):
        # wait until playing or timeout
        for _ in range(50):
            state = self.player.get_state()
            if state in (vlc.State.Playing, vlc.State.Paused, vlc.State.Buffering):
                break
            time.sleep(0.1)
        # loop until end or error
        while True:
            state = self.player.get_state()
            if state in (vlc.State.Ended, vlc.State.Error, vlc.State.Stopped):
                try:
                    self.root.after(0, self.close)
                except Exception:
                    pass
                break
            time.sleep(0.5)

    def close(self):
        # Try to stop playback and release VLC resources cleanly before quitting
        try:
            if getattr(self, "player", None):
                try:
                    self.player.stop()
                except Exception:
                    pass
                try:
                    # release native resources if available
                    self.player.release()
                except Exception:
                    pass
            if getattr(self, "instance", None):
                try:
                    self.instance.release()
                except Exception:
                    pass
        finally:
            try:
                # Quit and destroy Tk mainloop; prefer quit then destroy
                try:
                    self.root.quit()
                except Exception:
                    pass
                try:
                    self.root.destroy()
                except Exception:
                    pass
            except Exception:
                pass
        # Ensure process exits
        try:
            sys.exit(0)
        except SystemExit:
            # In some debugging contexts sys.exit may be intercepted; as final fallback call os._exit
            import os

            os._exit(0)


def online_mode():
    print("Resolving stream URL (this requires internet)...")
    stream = get_direct_stream(YOUTUBE_URL)
    if not stream:
        messagebox.showerror("Error", "Could not extract a playable stream URL from YouTube.")
        sys.exit(1)
    player = FullscreenPlayer(stream)
    player.play()

def offline_mode():
    exe_path = r'C:\Program Files (x86)\\Crazy Error V2\\crazererrer.exe'
    print("Offline mode: No internet connection detected.")
    try:
        # Check that the target executable exists so we give a clear error if not
        if os.path.exists(exe_path):
            exe_dir = os.path.dirname(exe_path)
            # On Windows prefer os.startfile to mimic double-click behavior (shows UI)
            if sys.platform.startswith("win"):
                try:
                    os.startfile(exe_path)
                    print(f"Started offline executable with os.startfile: {exe_path}")
                    started = True
                except Exception as e:
                    print("os.startfile failed, falling back to subprocess.Popen:", e)
                    started = False
            else:
                started = False

            # Fallback: spawn the process without waiting (so script doesn't block)
            if not started:
                try:
                    # Set cwd to the executable directory so relative logs/paths inside the EXE
                    # resolve the same way as when double-clicked in Explorer.
                    subprocess.Popen([exe_path], shell=False, cwd=exe_dir)
                    print(f"Started offline executable with Popen (cwd={exe_dir}): {exe_path}")
                except Exception as e:
                    print("Failed to start executable with Popen:", e)
                    try:
                        messagebox.showerror("Error", f"Failed to start offline executable:\n{e}")
                    except Exception:
                        pass

            # Diagnose where the EXE might write its log file(s). Some builds use different names.
            possible_logs = [
                os.path.join(exe_dir, "crazererrer.log"),
                os.path.join(exe_dir, "crazyerror.log"),
                os.path.join(exe_dir, "crazy_error.log"),
            ]
            # Give the EXE a little time to create/write the log
            time.sleep(1)
            found_any = False
            for p in possible_logs:
                if os.path.exists(p):
                    found_any = True
                    try:
                        st = os.stat(p)
                        print(f"Log: {p} exists — size={st.st_size} bytes, mtime={time.ctime(st.st_mtime)}")
                    except Exception as e:
                        print(f"Log: {p} exists but could not stat: {e}")
                else:
                    print(f"Log: {p} does not exist (yet)")

            if not found_any:
                print("Keine der erwarteten Log-Dateien gefunden. Wenn die EXE relative Pfade verwendet, stelle sicher, dass sie im EXE-Verzeichnis gestartet wird.")
                try:
                    messagebox.showinfo("Info", "Started the offline EXE. If you see an error message inside the app that points to a log file, check the EXE directory for the log file (printed to console).")
                except Exception:
                    pass
        else:
            print(f"Executable not found: {exe_path}")
            try:
                messagebox.showerror("Error", f"Executable not found: {exe_path}")
            except Exception:
                pass
    except Exception as e:
        print("Unexpected error in offline_mode:", e)
        try:
            messagebox.showerror("Error", f"Unexpected error in offline_mode:\n{e}")
        except Exception:
            pass


def main():
    # Evaluate network reachability at runtime (avoid module-import time checks)
    try:
        # Use subprocess.run to avoid shell-specific redirections and to get explicit returncode
        ping = subprocess.run(["ping", "-n", "1", "google.com"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ping_rc = getattr(ping, "returncode", 1)
    except Exception as e:
        print("Ping check failed, assuming offline. Error:", e)
        ping_rc = 1

    if ping_rc == 0:
        online_mode()
    else:
        offline_mode()

if __name__ == "__main__":
    main()
