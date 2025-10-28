import sys
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

YOUTUBE_URL = "https://youtu.be/xYjLtPQchN0?si=siAMkVqPqYefNyeJ"


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


def main():
    print("Resolving stream URL (this requires internet)...")
    stream = get_direct_stream(YOUTUBE_URL)
    if not stream:
        messagebox.showerror("Error", "Could not extract a playable stream URL from YouTube.")
        sys.exit(1)
    player = FullscreenPlayer(stream)
    player.play()


if __name__ == "__main__":
    main()