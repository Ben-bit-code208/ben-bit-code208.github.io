# ben_full_synth_with_presets_and_queue.py
# Ben's Mega Synth – UI+Preset Editor+Export Queue

import os
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

import glob
from pyo import *
import pyo
import random
import time
import threading
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog, messagebox
import json

global SineTable

try:
    import vlc
    from vlc import *
except ImportError:
    print("[Warning] VLC not available")

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False
    sd = None

try:
    import ctypes
    def msgbox(text, title="DEBUG"):
        try:
            ctypes.windll.user32.MessageBoxW(0, str(text), str(title), 0)
        except Exception:
            print(f"{title}: {text}")
except Exception:
    def msgbox(text, title="DEBUG"):
        print(f"{title}: {text}")

# ---------------- Constants & Helpers ----------------
MAX_INST = 14
PRESET_FILE = "presets.json"

ROOTS = [48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67]
SCALES = {
    "Major":        [0,2,4,5,7,9,11],
    "Minor":        [0,2,3,5,7,8,10],
    "Pentatonic":   [0,2,4,7,9],
    "Hirajoshi":    [0,2,3,7,8],
    "Dorian":       [0,2,3,5,7,9,10],
    "Mixolydian":   [0,2,4,5,7,9,10]
}

DEFAULT_PRESETS = {
    "Pad":  {"attack":0.5, "decay":0.8, "sustain":0.7, "release":1.2, "mul":0.5},
    "Bass": {"attack":0.01,"decay":0.1, "sustain":0.9, "release":0.3, "mul":0.9},
    "Pluck":{"attack":0.001,"decay":0.05,"sustain":0.0, "release":0.2, "mul":0.6},
    "Lead": {"attack":0.01, "decay":0.05,"sustain":0.8,"release":0.3, "mul":0.4},
    "Noise":{"attack":0.001,"decay":0.05,"sustain":0.0,"release":0.1, "mul":0.5},
    "Ambient Cloud": {"attack":1.2,"decay":1.0,"sustain":0.9,"release":2.5,"mul":0.35},
    "Chiptune Bassline": {"attack":0.001,"decay":0.02,"sustain":0.7,"release":0.08,"mul":0.9}
}

if not os.path.exists(PRESET_FILE):
    with open(PRESET_FILE, "w") as f:
        json.dump(DEFAULT_PRESETS, f, indent=2)


def mtof(m):
    return 440.0 * (2 ** ((m - 69) / 12.0))


def parse_code(code):
    s = str(code).zfill(7)
    inst = int(s[0:2])
    wave_type = int(s[2:4]) % 4
    length = max(int(s[4:7]), 1)
    inst = max(1, min(inst, MAX_INST))
    return inst, wave_type, length, s


def make_scale(root_midi, scale_name):
    ints = SCALES.get(scale_name, SCALES["Major"])
    return [root_midi + i for i in ints]


def chord_from_scale(scale_notes, degree, oct_shift=0):
    degree = degree % len(scale_notes)
    root = scale_notes[degree] + 12*oct_shift
    third = scale_notes[(degree+2) % len(scale_notes)] + 12*oct_shift
    fifth = scale_notes[(degree+4) % len(scale_notes)] + 12*oct_shift
    return [root, third, fifth]


def compute_complexity(code_int):
    """Compute complexity value from code (0.0 to 1.0)"""
    s = str(code_int).zfill(7)
    digit_sum = sum(int(d) for d in s)
    return min(1.0, digit_sum / 63.0)


class ChaosBrake:
    """Clamp complexity values"""
    def clamp(self, value, min_val=0.0, max_val=1.0):
        return max(min_val, min(max_val, value))


def chord_extensions(root_note, complexity):
    """Generate chord extensions based on complexity"""
    extensions = [root_note, root_note + 4, root_note + 7]  # Major triad
    if complexity > 0.3:
        extensions.append(root_note + 11)  # Add 7th
    if complexity > 0.6:
        extensions.append(root_note + 14)  # Add 9th
    return extensions


def melody_step(scale, current_step, complexity, rng):
    """Generate melodic note based on scale and complexity"""
    if complexity < 0.3:
        # Simple: stepwise motion
        return scale[current_step % len(scale)]
    elif complexity < 0.7:
        # Medium: small jumps
        offset = rng.choice([-2, -1, 0, 1, 2])
        idx = (current_step + offset) % len(scale)
        return scale[idx]
    else:
        # Complex: random jumps
        return rng.choice(scale)


class DrumEngine:
    """Simple drum pattern generator"""
    def __init__(self, complexity, seed=0):
        self.complexity = complexity
        self.rng = random.Random(seed)
    
    def patterns(self):
        """Return kick, snare, hat patterns (placeholder)"""
        kick = [1, 0, 0, 0, 1, 0, 0, 0]
        snare = [0, 0, 1, 0, 0, 0, 1, 0]
        hat = [1, 1, 1, 1, 1, 1, 1, 1]
        return kick, snare, hat


def midiToHz(midi_note):
    """Convert MIDI note to frequency"""
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


# ---------------- Synth Engine ----------------
class BenSynth:
    def __init__(self):
        self.server = None
        self.voices = []
        self.oscillators = []
        self.envs = []
        self.effects = []
        self.mix = None
        self.pat = None
        self.mel_pat = None
        self.drum_pat = None
        self.is_running = False
        self.server_ready = False
        self.init_thread = None
        self.volume_scales = []
        self.scope = None
        self.spec = None
        
        self.start_background_init()

    def start_background_init(self):
        if self.init_thread is None or not self.init_thread.is_alive():
            self.init_thread = threading.Thread(target=self._init_server_background, daemon=True)
            self.init_thread.start()
    
    def _init_server_background(self):
        try:
            try_configs = [
                {"buffersize": 2048, "sr": 44100},
                {"buffersize": 1024, "sr": 44100},
                {"buffersize": 512, "sr": 44100},
                {},
            ]
            
            for cfg in try_configs:
                try:
                    if cfg:
                        self.server = Server(**cfg)
                        print(f"[Info] Server object created with cfg={cfg}")
                    else:
                        self.server = Server()
                        print("[Info] Server object created with default settings")
                    self.server_ready = True
                    print("[Info] Background server preparation complete")
                    return
                except Exception as e:
                    print(f"[Debug] Server creation attempt failed: {e}")
                    self.server = None
            
            print("[Warning] Could not prepare Server object")
            self.server_ready = False
        except Exception as e:
            print(f"[Warning] Background server prep failed: {e}")
            self.server_ready = False
    
    def wait_for_server(self, timeout=15):
        start_time = time.time()
        while not self.server_ready and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        if not self.server_ready:
            print("[Warning] Server initialization timed out")
            self.start_server("dummy_init.wav")
            self.server_ready = True

    def __del__(self):
        try:
            self.stop_server()
        except Exception:
            pass

    def start_server(self, record_file):
        if self.server is not None and not self.server.getIsBooted():
            print("[Info] Using pre-created Server object")
        elif self.server is None:
            try_configs = [
                {"buffersize": 2048, "sr": 44100},
                {"buffersize": 1024, "sr": 44100},
                {"buffersize": 512, "sr": 44100},
                {},
            ]
            
            for cfg in try_configs:
                try:
                    if cfg:
                        self.server = Server(**cfg)
                    else:
                        self.server = Server()
                    break
                except Exception as e:
                    print(f"[Debug] Server creation failed: {e}")
                    self.server = None
            
            if self.server is None:
                raise RuntimeError("Server creation failed")
        
        attempts = 3
        for attempt in range(1, attempts + 1):
            try:
                self.server.recordOptions(filename=record_file, fileformat=0, sampletype=0)
                
                if not self.server.getIsBooted():
                    self.server.boot()
                    time.sleep(0.15)

                if not self.server.getIsStarted():
                    self.server.start()
                
                time.sleep(0.1)
                self.server.recstart()
                break
            except Exception as e:
                print(f"[Warning] Attempt {attempt} failed: {e}")
                if attempt == attempts:
                    raise

    def stop_server(self):
        if self.server is not None:
            try:
                self.server.recstop()
            except Exception as e:
                print(f"[Debug] recstop: {e}")
            
            time.sleep(0.1)
            
            try:
                self.server.stop()
            except Exception as e:
                print(f"[Debug] stop: {e}")
            
            time.sleep(0.05)
            
            try:
                self.server.shutdown()
            except Exception as e:
                print(f"[Debug] shutdown: {e}")
            finally:
                self.server = None

    def build_and_play(self, code, scale_name="Major", tempo_override=None,
                   gb_mode=False, preset_name="Pad", reverb_amount=0.4, delay_amount=0.2,
                   bitcrush_amount=0.0, export_file="out.wav", drums_on=True,
                   gui_callback=None, length_override=None):
        # === SAFE, ORDERED MULTI-VOICE VERSION ===
        
        # --- PARSE CODE ---
        try:
            code_int = int(code)
        except Exception:
            code_int = 0
        
        inst_count, wave_type, length, s = parse_code(code_int)
        if length_override is not None:
            length = int(length_override)
        
        # --- COMPLEXITY ---
        cx = compute_complexity(code_int)
        cx = ChaosBrake().clamp(cx)
        
        # --- TEMPO / SCALE ---
        tempo = tempo_override if tempo_override else 90 + int(cx * 40)
        beat_time = 60.0 / tempo
        scale = SCALES.get(scale_name, SCALES["Major"])
        root_note = 48
        
        # --- START SERVER ---
        if gui_callback:
            gui_callback("Starting audio engine...")
        self.start_server(export_file)
        
        # --- VOICE COUNT ---
        voice_count = min(2 + int(cx * 3), 5)
        voices = []
        
        # --- WAVE TABLE ---
        if wave_type == 0:
            table = SineTable()
        elif wave_type == 1:
            table = SquareTable()
        elif wave_type == 2:
            table = SawTable()
        else:
            table = SineTable()
        
        # --- BASS ---
        bass = Osc(table, freq=midiToHz(root_note), mul=0.25)
        voices.append(bass)
        
        # --- CHORDS ---
        if voice_count >= 3:
            for n in chord_extensions(root_note, cx):
                voices.append(Osc(table, freq=midiToHz(n), mul=0.08))
        
        # --- LEAD ---
        lead = None
        if voice_count >= 4:
            lead = Osc(table, freq=midiToHz(root_note + 12), mul=0.18)
            voices.append(lead)
        
        # --- TEXTURE ---
        if voice_count >= 5:
            voices.append(ButLP(Noise(0.02), freq=800 + cx * 1200))
        
        # --- DRUMS ---
        kick_pat = None
        snare_pat = None
        hat_pat = None
        if drums_on:
            drum_engine = DrumEngine(cx, seed=code_int % 1000)
            kick, snare, hat = drum_engine.patterns()
            
            # Kick drum
            def play_kick():
                k = Sine(freq=60, mul=0.8)
                kenv = Adsr(0.001, 0.03, 0.0, 0.05, mul=0.9)
                kick_voice = ButLP(k * kenv, freq=120).out()
                kenv.play()
            
            # Snare drum
            def play_snare():
                s = Noise(mul=0.6)
                senv = Adsr(0.001, 0.02, 0.0, 0.08, mul=0.7)
                snare_voice = ButBP(s * senv, freq=1800, q=0.6).out()
                senv.play()
            
            # Hi-hat
            def play_hat():
                h = Noise(mul=0.3)
                henv = Adsr(0.001, 0.01, 0.0, 0.02, mul=0.4)
                hat_voice = ButHP(h * henv, freq=6000).out()
                henv.play()
            
            kick_pat = Pattern(play_kick, time=beat_time).play()
            snare_pat = Pattern(play_snare, time=beat_time * 2).play()
            hat_pat = Pattern(play_hat, time=beat_time / 2).play()
        
        # --- MIX / FX ---
        mix = Mix(voices, voices=2)
        if reverb_amount > 0:
            mix = Freeverb(mix, size=0.8, damp=0.5, bal=reverb_amount)
        if delay_amount > 0:
            mix = Delay(mix, delay=beat_time * 0.75, feedback=0.3, mul=1)
        
        # Apply bitcrush if needed
        if gb_mode or bitcrush_amount > 0.0:
            if gb_mode:
                mix = Degrade(mix, bitdepth=6, srscale=0.125)
            else:
                mix = Degrade(mix, bitdepth=max(1, int(16 - bitcrush_amount*15)), 
                             srscale=1.0 - bitcrush_amount*0.5)
        
        mix.out()
        
        # --- SEQUENCER ---
        step = [0]
        rng = random.Random(code_int)
        
        def tick():
            deg = scale[(step[0] // 4) % len(scale)]
            bass.freq = midiToHz(root_note + deg)
            if lead is not None:
                note = melody_step(scale, step[0] % len(scale), cx, rng)
                lead.freq = midiToHz(root_note + note + 12)
            step[0] += 1
        
        pat = Pattern(tick, time=beat_time / 4).play()
        
        # Store patterns for cleanup
        self.pat = pat
        self.drum_pat = kick_pat
        self.is_running = True
        
        if gui_callback:
            gui_callback(f"Playing {length}s at {tempo} BPM – recording to {export_file}")
        
        # --- STOP ---
        def stop():
            try:
                pat.stop()
                if kick_pat:
                    kick_pat.stop()
                if snare_pat:
                    snare_pat.stop()
                if hat_pat:
                    hat_pat.stop()
            except Exception as e:
                print(f"[Debug] Pattern stop error: {e}")
            
            try:
                fade = Fader(fadein=0.01, fadeout=0.5, dur=0.6).play()
                time.sleep(0.6)
            except Exception:
                pass
            
            self.stop_server()
            self.is_running = False
            if gui_callback:
                gui_callback(f"Finished – saved {export_file}")
        
        CallAfter(stop, time=length)


# ---------------- GUI ----------------
class FullGUI:
    def __init__(self):
        self.synth = BenSynth()
        self.root = tk.Tk()
        self.root.title("Ben's Synth – Presets & Queue")
        self.root.geometry("800x600")

        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=8, pady=6)
        ttk.Label(top, text="7-stellige Zahl:").pack(side="left")
        self.code_entry = ttk.Entry(top, width=16, font=("Consolas", 12))
        self.code_entry.pack(side="left", padx=6)
        self.random_btn = ttk.Button(top, text="Random", command=self.set_random)
        self.random_btn.pack(side="left")

        body = ttk.Frame(self.root)
        body.pack(fill="both", expand=True, padx=8, pady=4)

        left = ttk.Frame(body)
        left.pack(side="left", fill="y", padx=(0,8))

        ttk.Label(left, text="Skala:").pack(anchor="w")
        self.scale_var = tk.StringVar(value="Major")
        self.scale_box = ttk.Combobox(left, textvariable=self.scale_var, values=list(SCALES.keys()), state="readonly", width=16)
        self.scale_box.pack(anchor="w", pady=2)

        ttk.Label(left, text="Preset:").pack(anchor="w", pady=(8,0))
        self.preset_var = tk.StringVar(value="Pad")
        self.preset_box = ttk.Combobox(left, textvariable=self.preset_var, values=self.load_preset_names(), state="readonly", width=18)
        self.preset_box.pack(anchor="w", pady=2)

        ps_frame = ttk.Frame(left)
        ps_frame.pack(anchor="w", pady=(8,2))
        ttk.Button(ps_frame, text="Save Preset...", command=self.save_preset_dialog).pack(side="left", padx=2)
        ttk.Button(ps_frame, text="Delete Preset", command=self.delete_preset).pack(side="left", padx=2)

        ttk.Label(left, text="Tempo (BPM):").pack(anchor="w", pady=(8,0))
        self.tempo_entry = ttk.Entry(left, width=10)
        self.tempo_entry.pack(anchor="w", pady=2)
        ttk.Label(left, text="Länge (s, optional):").pack(anchor="w", pady=(6,0))
        self.length_entry = ttk.Entry(left, width=10)
        self.length_entry.pack(anchor="w", pady=2)

        self.gb_var = tk.BooleanVar(value=False)
        self.drum_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left, text="Gameboy Mode", variable=self.gb_var).pack(anchor="w", pady=4)
        ttk.Checkbutton(left, text="Drums", variable=self.drum_var).pack(anchor="w", pady=2)

        ttk.Label(left, text="Reverb:").pack(anchor="w", pady=(8,0))
        self.rev_scale = ttk.Scale(left, from_=0.0, to=0.95, value=0.4, orient="horizontal", length=160)
        self.rev_scale.pack(anchor="w")
        ttk.Label(left, text="Delay:").pack(anchor="w", pady=(6,0))
        self.dly_scale = ttk.Scale(left, from_=0.0, to=0.95, value=0.2, orient="horizontal", length=160)
        self.dly_scale.pack(anchor="w")
        ttk.Label(left, text="Bitcrush:").pack(anchor="w", pady=(6,0))
        self.bit_scale = ttk.Scale(left, from_=0.0, to=1.0, value=0.0, orient="horizontal", length=160)
        self.bit_scale.pack(anchor="w")

        ttk.Label(left, text="Export filename:").pack(anchor="w", pady=(8,0))
        self.filename_entry = ttk.Entry(left, width=24)
        self.filename_entry.insert(0, "out.wav")
        self.filename_entry.pack(anchor="w", pady=2)

        btns = ttk.Frame(left)
        btns.pack(anchor="w", pady=8)
        ttk.Button(btns, text="Start (Play & Record)", command=self.on_start).pack(side="left", padx=2)
        ttk.Button(btns, text="Stop", command=self.on_stop).pack(side="left", padx=2)
        ttk.Button(btns, text="Show Scope", command=self.show_scope).pack(side="left", padx=2)

        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(right, text="Export Queue (numbers):").pack(anchor="w")
        self.queue_list = tk.Listbox(right, height=12)
        self.queue_list.pack(fill="both", expand=True, pady=4)

        qbtns = ttk.Frame(right)
        qbtns.pack(fill="x")
        ttk.Button(qbtns, text="Add Current", command=self.add_current_to_queue).pack(side="left", padx=4)
        ttk.Button(qbtns, text="Remove Selected", command=self.remove_selected_queue).pack(side="left", padx=4)
        ttk.Button(qbtns, text="Render Queue", command=self.render_queue).pack(side="left", padx=4)
        ttk.Button(qbtns, text="Save Queue...", command=self.save_queue).pack(side="left", padx=4)

        self.status_var = tk.StringVar(value="Audio engine initializing in background...")
        ttk.Label(self.root, textvariable=self.status_var).pack(fill="x", pady=(6,4))

        demo = ttk.Frame(self.root)
        demo.pack(fill="x", padx=8)
        ttk.Label(demo, text="Demo Presets:").pack(side="left")
        self.demo_box = ttk.Combobox(demo, values=list(DEFAULT_PRESETS.keys()), state="readonly")
        self.demo_box.pack(side="left", padx=6)
        ttk.Button(demo, text="Apply Demo", command=self.apply_demo).pack(side="left")
        
        self.root.after(100, self._check_server_ready)

    def load_preset_names(self):
        try:
            with open(PRESET_FILE, "r") as f:
                data = json.load(f)
                return sorted(list(data.keys()))
        except Exception:
            return list(DEFAULT_PRESETS.keys())

    def save_preset_dialog(self):
        name = simpledialog.askstring("Preset name", "Enter preset name:")
        if not name:
            return
        try:
            with open(PRESET_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = DEFAULT_PRESETS.copy()
        
        preset = {
            "attack": float(0.1),
            "decay": float(0.3),
            "sustain": float(0.7),
            "release": float(0.5),
            "mul": float(0.5)
        }
        
        cur = self.preset_var.get()
        if cur:
            p = data.get(cur)
            if p:
                preset.update(p)
        
        data[name] = preset
        with open(PRESET_FILE, "w") as f:
            json.dump(data, f, indent=2)
        self.preset_box['values'] = self.load_preset_names()
        self.preset_var.set(name)
        self.update_status(f"Saved preset '{name}'")

    def delete_preset(self):
        cur = self.preset_var.get()
        if not cur:
            return
        if messagebox.askyesno("Delete", f"Delete preset '{cur}'?"):
            try:
                with open(PRESET_FILE, "r") as f:
                    data = json.load(f)
                if cur in data:
                    del data[cur]
                    with open(PRESET_FILE, "w") as f:
                        json.dump(data, f, indent=2)
                self.preset_box['values'] = self.load_preset_names()
                self.preset_var.set("")
                self.update_status(f"Deleted preset {cur}")
            except Exception as e:
                self.update_status(f"Error deleting: {e}")

    def add_current_to_queue(self):
        user = self.code_entry.get().strip()
        if user == "":
            user = str(random.randint(1000000, 9999999))
            self.code_entry.delete(0, tk.END)
            self.code_entry.insert(0, user)
        try:
            v = int(user)
            self.queue_list.insert(tk.END, str(v))
            self.update_status(f"Added {v} to queue")
        except Exception:
            self.update_status("Invalid number – must be integer")

    def remove_selected_queue(self):
        sel = list(self.queue_list.curselection())
        for i in reversed(sel):
            self.queue_list.delete(i)
        self.update_status("Removed selected from queue")

    def save_queue(self):
        path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text','*.txt')])
        if not path:
            return
        items = self.queue_list.get(0, tk.END)
        with open(path, 'w') as f:
            for it in items:
                f.write(str(it) + "\n")
        self.update_status(f"Queue saved to {path}")

    def render_queue(self):
        items = self.queue_list.get(0, tk.END)
        if not items:
            self.update_status("Queue empty")
            return
        fname_base = self.filename_entry.get().strip() or "out.wav"
        
        if not messagebox.askyesno("Render Queue", f"Render {len(items)} items sequentially?"):
            return
        
        def worker():
            for idx, it in enumerate(items):
                code = int(it)
                outname = f"{os.path.splitext(fname_base)[0]}_{idx+1}.wav"
                self.update_status(f"Rendering {it} -> {outname}")
                settings = self.collect_ui()
                self.synth.build_and_play(code,
                                          scale_name=settings['scale'],
                                          tempo_override=settings['tempo'],
                                          gb_mode=settings['gb'],
                                          preset_name=settings['preset'],
                                          reverb_amount=settings['rev'],
                                          delay_amount=settings['dly'],
                                          bitcrush_amount=settings['bit'],
                                          export_file=outname,
                                          drums_on=settings['drums'],
                                          gui_callback=self.update_status,
                                          length_override=settings['length'])
            self.update_status("Queue finished")
        threading.Thread(target=worker, daemon=True).start()

    def collect_ui(self):
        scale_name = self.scale_var.get() or 'Major'
        preset = self.preset_var.get() or 'Pad'
        tempo = None
        t = self.tempo_entry.get().strip()
        if t:
            try:
                tempo = int(t)
            except:
                tempo = None
        length = None
        L = self.length_entry.get().strip()
        if L:
            try:
                length = int(L)
            except:
                length = None
        gb = self.gb_var.get()
        drums = self.drum_var.get()
        rev = float(self.rev_scale.get())
        dly = float(self.dly_scale.get())
        bit = float(self.bit_scale.get())
        return {
            'scale': scale_name, 
            'preset': preset, 
            'tempo': tempo, 
            'length': length, 
            'gb': gb, 
            'drums': drums, 
            'rev': rev, 
            'dly': dly, 
            'bit': bit
        }

    def on_start(self):
        if self.synth.is_running:
            self.update_status("Already playing")
            return
        user = self.code_entry.get().strip()
        if user == "":
            user = random.randint(1000000, 9999999)
            self.code_entry.delete(0, tk.END)
            self.code_entry.insert(0, str(user))
        try:
            code = int(user)
        except Exception:
            self.update_status("Invalid number")
            return
        settings = self.collect_ui()
        outname = self.filename_entry.get().strip() or 'out.wav'
        self.update_status("Starting...")
        threading.Thread(target=self.synth.build_and_play, kwargs={
            'code': code,
            'scale_name': settings['scale'],
            'tempo_override': settings['tempo'],
            'gb_mode': settings['gb'],
            'preset_name': settings['preset'],
            'reverb_amount': settings['rev'],
            'delay_amount': settings['dly'],
            'bitcrush_amount': settings['bit'],
            'export_file': outname,
            'drums_on': settings['drums'],
            'gui_callback': self.update_status,
            'length_override': settings['length']
        }, daemon=True).start()

    def on_stop(self):
        if self.synth.is_running:
            self.update_status("Stopping...")
            self.synth.stop_server()
            self.synth.is_running = False
            self.update_status("Stopped")
        else:
            self.update_status("Nothing to stop")

    def show_scope(self):
        if not self.synth.server:
            try:
                s = Server()
                s.boot()
                s.start()
                t = SquareTable()
                o = Osc(table=t, freq=220, mul=0.02).out()
                try:
                    Scope(o)
                    Spectrum(o)
                except Exception:
                    pass
                time.sleep(0.25)
                try:
                    o.stop()
                except Exception:
                    pass
                try:
                    s.recstop()
                except Exception:
                    pass
                s.stop()
                s.shutdown()
                self.update_status("Temporary scope shown")
            except Exception as e:
                self.update_status(f"Scope error: {e}")
        else:
            self.update_status("Scope should be visible (if supported)")

    def set_random(self):
        r = random.randint(1000000, 9999999)
        self.code_entry.delete(0, tk.END)
        self.code_entry.insert(0, str(r))
        self.update_status(f"Random code: {r}")

    def update_status(self, text):
        def set_text():
            self.status_var.set(text)
        self.root.after(0, set_text)
    
    def _check_server_ready(self):
        if self.synth.server_ready:
            self.update_status("Bereit - Audio engine ready")
        else:
            self.update_status("Audio engine initializing...")
            self.root.after(500, self._check_server_ready)

    def apply_demo(self):
        name = self.demo_box.get()
        if not name:
            return
        try:
            with open(PRESET_FILE, 'r') as f:
                data = json.load(f)
        except Exception:
            data = DEFAULT_PRESETS
        demo = data.get(name) or DEFAULT_PRESETS.get(name)
        if not demo:
            self.update_status('Demo not found')
            return
        vals = list(self.preset_box['values'])
        if name not in vals:
            vals = vals + [name]
            self.preset_box['values'] = vals
        self.preset_var.set(name)
        self.update_status(f"Applied demo preset: {name}")


# ---------------- Main ----------------
if __name__ == "__main__":
    try:
        gui = FullGUI()
        gui.root.mainloop()
    except Exception as e:
        import traceback
        print(f"FATAL ERROR: {e}")
        traceback.print_exc()
        exit(1)