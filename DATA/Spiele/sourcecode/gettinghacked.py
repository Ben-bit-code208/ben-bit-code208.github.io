# gettinghacked_clean.py
import sys
import os
import threading
import time
import tkinter as tk
from tkinter import messagebox
from yt_dlp import YoutubeDL
import vlc

YOUTUBE_URL = "https://youtu.be/xYjLtPQchN0?si=siAMkVqPqYefNyeJ"

def get_direct_stream(url: str) -> str | None:
    """Extrahiert eine direkte Stream-URL mit yt_dlp (falls möglich)."""
    opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        print("yt_dlp failed:", e)
        return None

    if not info:
        return None
    if info.get("url"):
        return info["url"]
    formats = info.get("formats") or []
    for f in sorted(formats, key=lambda x: (x.get("height") or 0), reverse=True):
        if f.get("ext", "").lower() in ("mp4", "m4v", "webm", "mkv") and f.get("acodec") != "none":
            return f.get("url")
    if formats:
        return formats[-1].get("url")
    return None

class FullscreenPlayer:
    def __init__(self, stream_url: str):
        self.stream_url = stream_url
        self.instance = self._create_vlc_instance()
        self.player = self.instance.media_player_new()
        self.root = tk.Tk()
        self.root.title("Cutscene")
        self.root.configure(bg="black")
        self.root.attributes("-fullscreen", True)
        self.root.config(cursor="none")
        self.root.bind("<Escape>", lambda e: self.close_and_exit())
        self.root.bind("<Button-1>", lambda e: self.close_and_exit())

        self.frame = tk.Frame(self.root, bg="black")
        self.frame.pack(fill=tk.BOTH, expand=1)
        self.root.after(0, self.set_window_handle_after_map)

        self.monitor_thread = threading.Thread(target=self.monitor_playback, daemon=True)

    def _create_vlc_instance(self):
        try:
            return vlc.Instance("--no-xlib", "--avcodec-hw=none")
        except TypeError:
            try:
                return vlc.Instance(["--no-xlib", "--avcodec-hw=none"])
            except Exception:
                return vlc.Instance("--no-xlib")

    def set_window_handle_after_map(self):
        try:
            self.root.update_idletasks()
            hwnd = self.frame.winfo_id()
            if sys.platform.startswith("win"):
                self.player.set_hwnd(hwnd)
            elif sys.platform.startswith("linux"):
                self.player.set_xwindow(hwnd)
            elif sys.platform == "darwin":
                self.player.set_nsobject(hwnd)
        except Exception:
            pass

    def monitor_playback(self):
        for _ in range(50):
            try:
                state = self.player.get_state()
            except Exception:
                state = None
            if state in (vlc.State.Playing, vlc.State.Paused, vlc.State.Buffering):
                break
            time.sleep(0.1)

        while True:
            try:
                state = self.player.get_state()
            except Exception:
                state = None
            if state in (vlc.State.Ended, vlc.State.Error, vlc.State.Stopped):
                self.root.after(0, self.close)
                break
            time.sleep(0.5)

    def play(self):
        try:
            media = self.instance.media_new(self.stream_url)
        except Exception:
            media = self.instance.media_new(self.stream_url)

        try:
            self.player.set_media(media)
            self.player.play()
        except Exception as e:
            messagebox.showerror("Playback error", f"Could not start playback: {e}")
            return

        try:
            em = self.player.event_manager()
            em.event_attach(vlc.EventType.MediaPlayerEndReached, lambda e: self.root.after(0, self.close))
            em.event_attach(vlc.EventType.MediaPlayerEncounteredError, lambda e: self.root.after(0, self.close))
            em.event_attach(vlc.EventType.MediaPlayerStopped, lambda e: self.root.after(0, self.close))
        except Exception:
            pass

        if not self.monitor_thread.is_alive():
            self.monitor_thread = threading.Thread(target=self.monitor_playback, daemon=True)
            self.monitor_thread.start()

        try:
            self.root.mainloop()
        except Exception:
            self.close()

    def close(self):
        try:
            if getattr(self, "player", None):
                self.player.stop()
                self.player.release()
            if getattr(self, "instance", None):
                self.instance.release()
        finally:
            try:
                self.root.quit()
                self.root.destroy()
            except Exception:
                pass

    def close_and_exit(self):
        self.close()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

def runhack():
    print("Resolving stream URL (this requires internet)...")
    stream = get_direct_stream(YOUTUBE_URL)
    if not stream:
        messagebox.showerror("Error", "Could not extract a playable stream URL from YouTube.")
        return
    player = FullscreenPlayer(stream)
    player.play()


if __name__ == "__main__":
    runhack()
