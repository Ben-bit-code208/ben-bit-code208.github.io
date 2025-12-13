# ben_full_synth_with_presets_and_queue.py
# Ben's Mega Synth — UI+Preset Editor+Export Queue
# Adds:
# - Preset save/load (JSON file presets.json)
# - Demo presets (several ready-to-use)
# - Preset editor (save current settings as new preset)
# - Export queue: queue multiple 7-digit numbers and render them sequentially
# - Slight UI polish and helpful messages

# Run: python ben_full_synth_with_presets_and_queue.py
# Requires: pyo, standard Python libs


# Set working directory to script directory for proper file/resource loading
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

import glob
from typing import Self
from pyo import *
import pyo
import random
import time
import threading
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog, messagebox
import json
import vlc
from vlc import *

# Try to import sounddevice for default device detection
try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False
    sd = None

global server
global parse_code
global code
global msgbox
global mtof
global make_scale
global chord_from_scale
global BenSynth
global FullGUI
global DEFAULT_PRESETS
global settings
global scale_name, tempo_override, gb_mode, preset_name, reverb_amount, delay_amount, bitcrush_amount,export_file,drums_on,gui_callback,length_override
global outname
global __init__
global worker
global collect_ui
global on_start
global on_stop
global show_scope
global set_random
global update_status
global apply_demo
global load_preset_names
global save_preset_dialog
global delete_preset
global add_current_to_queue
global remove_selected_queue
global save_queue
global render_queue
global rhythm
global melody
global drum_step
global build_and_play
global start_server
global stop_server
global self

import ctypes

def msgbox(text, title="DEBUG"):
    try:
        ctypes.windll.user32.MessageBoxW(0, str(text), str(title), 0)
    except Exception:
        pass

# ---------------- Constants & Helpers ----------------
MAX_INST = 14  # safe upper bound
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
    # Demo presets
    "Ambient Cloud": {"attack":1.2,"decay":1.0,"sustain":0.9,"release":2.5,"mul":0.35},
    "Chiptune Bassline": {"attack":0.001,"decay":0.02,"sustain":0.7,"release":0.08,"mul":0.9}
}

# Make sure presets file exists
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
        
        # Start server initialization in background immediately
        self.start_background_init()

    def start_background_init(self):
        #Initialize audio server in background thread#
        if self.init_thread is None or not self.init_thread.is_alive():
            self.init_thread = threading.Thread(target=self._init_server_background, daemon=True)
            self.init_thread.start()
    
    def _init_server_background(self):
        # Background thread: initialize pyo server structure (but don't boot yet)
        try:
            # Just create the Server object, don't boot/start it yet
            # This prepares it for quick startup when actually needed
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
                        print(f"[Info] Server object created (not booted yet) with cfg={cfg}")
                    else:
                        self.server = Server()
                        print("[Info] Server object created (not booted yet) with default settings")
                    self.server_ready = True
                    print("[Info] Background server preparation complete - ready to boot on demand")
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
        # Wait for background server initialization to complete
        start_time = time.time()
        while not self.server_ready and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        if not self.server_ready:
            print("[Warning] Server initialization timed out, retrying...")
            self.start_server("dummy_init.wav")
            self.server_ready = True

    def __del__(self):
        # Ensure proper cleanup to avoid pyo Server errors on shutdown
        try:
            self.stop_server()
        except Exception:
            pass

    def start_server(self, record_file):
        # If server was pre-created but not booted, just boot it now
        # Otherwise create fresh
        if self.server is not None and not self.server.getIsBooted():
            # Use pre-created server from background init
            print("[Info] Using pre-created Server object, booting now...")
        elif self.server is None:
            # Create fresh Server
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
                        print(f"[Info] Server created with cfg={cfg} (cooperative mode)")
                    else:
                        self.server = Server()
                        print("[Info] Server created with default settings (cooperative mode)")
                    break
                except Exception as e:
                    print(f"[Debug] Server creation attempt failed: {e}")
                    self.server = None
            
            if self.server is None:
                print("[Error] Could not create Server")
                raise RuntimeError("Server creation failed")
        
        # Now boot and start (whether fresh or pre-created)
        attempts = 3
        backoff = 0.15
        last_exc = None
        for attempt in range(1, attempts + 1):
            try:
                self.server.recordOptions(filename=record_file, fileformat=0, sampletype=0)
                print("[Info] Record options set")

                if not getattr(self.server, 'getIsBooted', lambda: False)():
                    self.server.boot()
                    print("[Info] Server booted")
                    time.sleep(0.15)

                # Try starting server using available getters if present
                started = False
                try:
                    if hasattr(self.server, 'getIsStarted'):
                        if not self.server.getIsStarted():
                            self.server.start()
                        started = True
                        method_used = 'getIsStarted'
                    elif hasattr(self.server, 'getIsRunning'):
                        if not self.server.getIsRunning():
                            self.server.start()
                        started = True
                        method_used = 'getIsRunning'
                    else:
                        # No getters present - just call start()
                        self.server.start()
                        started = True
                        method_used = 'start()'
                except Exception as e:
                    # If any getter raised, attempt a direct start()
                    try:
                        self.server.start()
                        started = True
                        method_used = 'start()-fallback'
                    except Exception as e2:
                        last_exc = e2

                if started:
                    print(f"[Info] Server started (method={method_used})")
                else:
                    raise RuntimeError(f"Server did not report started; last_exc={last_exc}")

                # Gentle recording start (non-fatal if it fails)
                try:
                    time.sleep(0.1)
                    self.server.recstart()
                    print("[Info] Recording started")
                except Exception as e:
                    print(f"[Warning] recstart had issues (non-fatal): {e}")

                # If we reached here, boot/start succeeded
                last_exc = None
                break
            except Exception as e:
                last_exc = e
                print(f"[Warning] Attempt {attempt} to boot/start server failed: {e}")
                try:
                    time.sleep(backoff * attempt)
                except Exception:
                    pass
                # On last attempt, cleanup and re-raise
                if attempt == attempts:
                    print(f"[Error] Server boot/start failed after {attempts} attempts: {last_exc}")
                    if self.server is not None:
                        try:
                            self.server.shutdown()
                        except Exception:
                            pass
                        self.server = None
                    raise

    def stop_server(self):
        #Stop and cleanup the audio server safely - release device gracefully#
        if self.server is not None:
            try:
                print("[Info] Stopping recording...")
                self.server.recstop()
            except Exception as e:
                print(f"[Debug] recstop: {e}")
            
            # Brief delay to flush audio buffers
            try:
                time.sleep(0.1)
            except Exception:
                pass
            
            try:
                print("[Info] Stopping playback...")
                self.server.stop()
            except Exception as e:
                print(f"[Debug] stop: {e}")
            
            # Graceful shutdown delay
            try:
                time.sleep(0.05)
            except Exception:
                pass
            
            try:
                print("[Info] Shutting down server...")
                self.server.shutdown()
            except Exception as e:
                print(f"[Debug] shutdown: {e}")
            finally:
                self.server = None
                print("[Info] Audio device released - other applications can use audio now")

    def build_and_play(self, code, scale_name="Major", tempo_override=None,
                       gb_mode=False, preset_name="Pad", reverb_amount=0.4, delay_amount=0.2,
                       bitcrush_amount=0.0, export_file="out.wav", drums_on=True,
                       gui_callback=None, length_override=None):
        # Wait for background server initialization to complete
        if gui_callback:
            gui_callback("Waiting for audio engine...")
        self.wait_for_server()
        if gui_callback:
            gui_callback("Audio engine ready, building...")
        
        inst_count, wave_type, length, s = parse_code(code)
        if length_override:
            length = length_override
        self.is_running = True
        if gui_callback:
            gui_callback(f"Building: instruments={inst_count}, wave={wave_type}, length={length}s")

        # tempo
        tempo = 60 + (int(s[1:3]) % 61)
        if tempo_override:
            tempo = max(20, min(300, tempo_override))
        beat = 60.0 / tempo

        # scale / root
        root_index = int(s[0]) % len(ROOTS)
        root_midi = ROOTS[root_index]
        scale = make_scale(root_midi, scale_name)

        # Deterministic RNG seeded by the 7-digit code string 's' so volumes are reproducible
        try:
            seed_val = int(s)
        except Exception:
            seed_val = 0
        local_rng = random.Random(seed_val)
        # reset per-run volume scales
        self.volume_scales = []

        # start server & recording
        try:
            self.start_server(export_file)
        except Exception as e:
            if gui_callback:
                gui_callback(f"Server start failed: {e}")
            self.is_running = False
            return

        # load preset
        try:
            with open(PRESET_FILE, "r") as f:
                presets = json.load(f)
        except Exception:
            presets = DEFAULT_PRESETS
        p = presets.get(preset_name, DEFAULT_PRESETS.get("Pad", DEFAULT_PRESETS[list(DEFAULT_PRESETS.keys())[0]]))

        # build voices
        self.voices = []
        self.envs = []
        self.effects = []
        self.oscillators = []  # Store oscillators for frequency control
        for i in range(inst_count):
            try:
                deg = (int(s[(2 + i) % len(s)]) + i) % len(scale)
                midi_note = scale[deg] + random.choice([0, 12, 0])
                freq = mtof(midi_note + random.choice([-12,0,12]))

                if gb_mode:
                    try:
                        table = SquareTable()
                        src = Osc(table=table, freq=freq, mul=0.38)
                    except Exception as e:
                        print(f"[Warning] GB mode Osc creation, falling back to Sine: {e}")
                        src = Sine(freq=freq, mul=0.28)  # Fallback
                else:
                    if wave_type == 0:
                        # Use Sine oscillator for sine wave
                        src = Sine(freq=freq, mul=0.28)
                    elif wave_type == 1:
                        try:
                            table = SquareTable()
                            src = Osc(table=table, freq=freq, mul=0.23)
                        except Exception as e:
                            print(f"[Warning] Square Osc creation, falling back to Sine: {e}")
                            src = Sine(freq=freq, mul=0.23)  # Fallback
                    elif wave_type == 2:
                        try:
                            table = SawTable()
                            src = Osc(table=table, freq=freq, mul=0.2)
                        except Exception as e:
                            print(f"[Warning] Saw Osc creation, falling back to Sine: {e}")
                            src = Sine(freq=freq, mul=0.2)  # Fallback
                    else:
                        src = Noise(mul=0.18)

                # preset ADSR with per-instrument volume driven by the code (deterministic)
                a = max(0.001, p.get("attack",0.01) * random.uniform(0.8, 1.2))
                d = p.get("decay",0.1) * random.uniform(0.8, 1.2)
                s_val = min(0.99, p.get("sustain",0.7) * random.uniform(0.9, 1.1))
                r = p.get("release",0.3) * random.uniform(0.8, 1.5)
                # Per-voice deterministic volume factor from seeded RNG
                vol_min = 0.35
                vol_max = 1.05
                vol_factor = vol_min + (local_rng.random() * (vol_max - vol_min))
                base_mul = p.get("mul", 0.5)
                env = Adsr(attack=a, decay=d, sustain=s_val, release=r, dur=length, mul=base_mul * vol_factor)
                sig = src * env
                # store for possible GUI display/automation
                try:
                    self.volume_scales.append(vol_factor)
                except Exception:
                    self.volume_scales = [vol_factor]

                # filters
                lp_cut = random.randint(300, 2500)
                hp_cut = random.randint(30, 400)
                sig = ButLP(sig, freq=lp_cut)
                sig = ButHP(sig, freq=hp_cut)

                # bitcrush / downsample if GB mode - amplified 8-bit effect
                if gb_mode or bitcrush_amount > 0.0:
                    if gb_mode:
                        # Aggressive gameboy mode: heavy bitcrush + extreme downsampling
                        bitdepth = 6  # 6-bit = authentic gameboy sound
                        srscale = 0.125  # 8x downsampling for retro 8-bit lo-fi
                        bit = Degrade(sig, bitdepth=bitdepth, srscale=srscale)
                        # Apply bitcrush twice for more harmonic distortion
                        bit = Degrade(bit, bitdepth=7, srscale=0.25)
                    else:
                        bit = Degrade(sig, bitdepth=max(1, int(16 - bitcrush_amount*15)), srscale=1.0 - bitcrush_amount*0.5)
                    sig = bit

                # Reverb & Delay chain (amounts controlled, but reduced for GB clarity)
                reverb_bal = reverb_amount * (0.3 if gb_mode else 1.0)  # Less reverb in GB mode for clarity
                rev = Freeverb(sig, size=0.8, damp=0.5, bal=reverb_bal)
                dly = Delay(rev, delay=beat * random.uniform(0.25, 1.0), feedback=delay_amount * (0.5 if gb_mode else 1.0), mul=0.7)
                chor = Chorus(dly, depth=random.uniform(0.3, 1.0) if gb_mode else random.uniform(0.5, 1.8), feedback=0.1 if gb_mode else 0.15, bal=0.2 if gb_mode else 0.3)

                self.voices.append(chor)
                self.envs.append(env)
                self.oscillators.append(src)  # Store oscillator for frequency control
                self.effects.append((rev, dly, chor))
            except Exception as e:
                print(f"[Warning] Voice {i} creation skipped: {e}")
                continue

        # Add extra instruments to enrich song-like texture
        try:
            # Pad: warm background (saw -> lowpass -> long ADSR)
            pad_base_note = scale[0] + 12  # one octave above root
            pad_freq = mtof(pad_base_note)
            try:
                pad_table = SawTable()
                pad_src = Osc(table=pad_table, freq=pad_freq, mul=0.4)
            except Exception:
                pad_src = Sine(freq=pad_freq, mul=0.35)
            pad_env = Adsr(attack=0.8, decay=1.2, sustain=0.7, release=2.5, dur=length, mul=0.5)
            pad_sig = ButLP(pad_src * pad_env, freq=900)
            pad_rev = Freeverb(pad_sig, size=0.9, damp=0.6, bal=reverb_amount*0.6)
            self.voices.append(pad_rev)
            self.envs.append(pad_env)
            self.oscillators.append(pad_src)
            self.volume_scales.append(0.8)

            # Vocal-like formant: square -> bandpass pair modulated by slow LFOs
            # Choose a lead note from the scale
            vocal_note = scale[min(len(scale)-1, max(0, int(local_rng.random()*len(scale))))] + 12
            vocal_freq = mtof(vocal_note)
            try:
                v_table = SquareTable()
                v_src = Osc(table=v_table, freq=vocal_freq, mul=0.35)
            except Exception:
                v_src = Sine(freq=vocal_freq, mul=0.3)
            # formant centers
            f1 = 400 + int(local_rng.random() * 400)
            f2 = 1200 + int(local_rng.random() * 800)
            lfo1 = Sine(freq=local_rng.uniform(0.08,0.18), mul=local_rng.uniform(30,120), add=f1)
            lfo2 = Sine(freq=local_rng.uniform(0.06,0.14), mul=local_rng.uniform(80,220), add=f2)
            v_sig = ButBP(v_src, freq=lfo1, q=6)
            v_sig = ButBP(v_sig, freq=lfo2, q=5)
            v_env = Adsr(attack=0.02, decay=0.15, sustain=0.6, release=0.6, dur=length, mul=0.55)
            v_out = Freeverb(v_sig * v_env, size=0.6, damp=0.4, bal=reverb_amount*0.5)
            self.voices.append(v_out)
            self.envs.append(v_env)
            self.oscillators.append(v_src)
            self.volume_scales.append(0.9)

            # Arpeggio layer: three quick voices that cycle through scale degrees
            arp_count = 3
            arp_osc = []
            arp_envs = []
            for ai in range(arp_count):
                try:
                    atable = SquareTable()
                    a_src = Osc(table=atable, freq=mtof(scale[ai % len(scale)] + 12), mul=0.18)
                except Exception:
                    a_src = Sine(freq=mtof(scale[ai % len(scale)] + 12), mul=0.14)
                a_env = Adsr(attack=0.005, decay=0.06, sustain=0.0, release=0.08, dur=length, mul=0.6)
                a_sig = ButHP(a_src * a_env, freq=400 + ai*120)
                a_sig = Delay(a_sig, delay=beat * (0.125 * (ai+1)), feedback=0.12, mul=0.6)
                self.voices.append(a_sig)
                self.envs.append(a_env)
                self.oscillators.append(a_src)
                self.volume_scales.append(0.7 - ai*0.1)
                arp_osc.append(a_src)
                arp_envs.append(a_env)

            # Arpeggio pattern (fast notes)
            def arp_step():
                try:
                    note = local_rng.choice(scale) + 12
                    for idx, o in enumerate(arp_osc):
                        try:
                            o.freq = mtof(note + idx*3)
                        except Exception:
                            pass
                        try:
                            arp_envs[idx].play()
                        except Exception:
                            pass
                except Exception:
                    pass
            Pattern(function=arp_step, time=beat*0.25).play()
        except Exception as e:
            print(f"[Warning] Extra instruments creation failed: {e}")

        # Mixer
        self.mix = Mix(self.voices, voices=2).out()

        # Scope & Spectrum
        try:
            self.scope = Scope(self.mix)
            self.spec = Spectrum(self.mix)
        except Exception:
            self.scope = None
            self.spec = None

        # Small delay to ensure audio objects are fully initialized before patterns start
        print(f"[Info] Waiting for audio initialization... (Bluetooth may need more time)")
        time.sleep(0.5)  # Increased delay for Bluetooth stability
        print(f"[Info] Audio ready with {len(self.oscillators)} voices")
        # Detailed diagnostics: for each voice print oscillator type, env mul, vol factor, and src mul
        try:
            diag_lines = []
            total_osc = len(self.oscillators)
            total_env = len(self.envs)
            total_vox = len(self.voices)
            diag_lines.append(f"Voices/osc/envs: {total_vox}/{total_osc}/{total_env}")
            for i in range(total_osc):
                try:
                    osc = self.oscillators[i]
                except Exception:
                    osc = None
                try:
                    env = self.envs[i]
                except Exception:
                    env = None
                # oscillator type
                try:
                    otype = type(osc).__name__ if osc is not None else 'None'
                except Exception:
                    otype = 'Unknown'
                # env mul (may be a pyo object or numeric)
                try:
                    env_mul = getattr(env, 'mul') if env is not None else None
                    # If env_mul is a pyo object, try to read value attribute
                    try:
                        env_mul_val = float(env_mul)
                    except Exception:
                        env_mul_val = str(env_mul)
                except Exception:
                    env_mul_val = None
                # recorded deterministic vol factor (if present)
                try:
                    vol_factor = self.volume_scales[i]
                except Exception:
                    vol_factor = None
                # oscillator initial mul (if present)
                try:
                    src_mul = getattr(osc, 'mul') if osc is not None else None
                    try:
                        src_mul_val = float(src_mul)
                    except Exception:
                        src_mul_val = str(src_mul)
                except Exception:
                    src_mul_val = None

                diag_lines.append(f"#{i}: osc={otype}, src_mul={src_mul_val}, env_mul={env_mul_val}, vol_factor={vol_factor}")

            # Summary of added layers (pad, vocal, arp) presence by checking names
            extra_info = []
            try:
                # detect presence by common class names or expected counts
                if total_vox > total_osc:
                    extra_info.append('More processed voices than raw oscillators (effects added)')
                if any(isinstance(v, Freeverb) or (type(v).__name__=='Freeverb') for v in self.voices):
                    extra_info.append('Reverb present')
                if any(type(v).__name__=='Delay' for v in self.voices):
                    extra_info.append('Delay present')
            except Exception:
                pass

            print("[Diagnostics] " + " | ".join(diag_lines))
            if extra_info:
                print("[Diagnostics-Extra] " + ", ".join(extra_info))

            # Also expose a compact per-voice volumes list for quick scanning
            try:
                vols = ", ".join([f"{(v if v is not None else 0):.2f}" for v in self.volume_scales])
                print(f"[Debug] Per-voice volumes: {vols}")
            except Exception:
                pass

            if gui_callback:
                # Show a short summary in GUI status bar
                try:
                    gui_callback(f"Audio ready: {len(self.oscillators)} voices ({len(self.voices)} processed). Vols: {', '.join([f'{(v if v is not None else 0):.2f}' for v in self.volume_scales])}")
                except Exception:
                    gui_callback(f"Audio ready: {len(self.oscillators)} voices")
        except Exception as e:
            print(f"[Debug] Could not display diagnostics: {e}")

        # Rhythm pattern with chord progression and bass backbone
        rhythm_count = [0]
        chord_prog = [0, 3, 4, 0]  # I-IV-V-I progression
        chord_idx = [0]
        beat_in_measure = [0]  # Track position in 4-beat measure
        
        def rhythm():
            rhythm_count[0] += 1
            beat_in_measure[0] = (rhythm_count[0] - 1) % 4
            
            if rhythm_count[0] == 1:
                print(f"[Info] Rhythm pattern started with chord progression and bass")
            if not self.oscillators or not self.envs:
                return
            
            # Update chord every 4 beats
            if beat_in_measure[0] == 0:
                prog_degree = chord_prog[chord_idx[0] % len(chord_prog)]
                chord_idx[0] += 1
            else:
                prog_degree = chord_prog[(chord_idx[0] - 1) % len(chord_prog)]
            
            chord = chord_from_scale(scale, prog_degree, oct_shift=0)
            
            # Structured rhythm: bass on beat 1 & 3, harmony on all beats, random fills
            if beat_in_measure[0] in [0, 2]:  # Beats 1 and 3 (bass hits)
                if len(self.oscillators) > 0:
                    try:
                        # Bass note: root of chord, down 2 octaves
                        bass_note = chord[0] - 24
                        self.oscillators[0].freq = mtof(bass_note)
                        self.envs[0].play()
                    except Exception:
                        pass
            
            # Harmony voices on all beats (with variation)
            num_voices = min(len(self.envs) - 1, max(1, (len(self.envs) - 1) // 3))
            if beat_in_measure[0] in [1, 3]:  # Beats 2 and 4: fewer voices for structure
                num_voices = max(1, num_voices // 2)
            
            harmony_range = range(1, min(len(self.oscillators), 1 + num_voices + 2))
            if harmony_range:
                hits = random.sample(list(harmony_range), min(num_voices, len(list(harmony_range))))
                for h in hits:
                    if h >= len(self.oscillators):
                        continue
                    try:
                        osc = self.oscillators[h]
                        if hasattr(osc, "freq"):
                            note = random.choice(chord)
                            octave_shift = random.choice([0, 0, 0, 12])  # Mostly same octave, rarely higher
                            osc.freq = mtof(note + octave_shift)
                    except Exception:
                        pass
                    try:
                        self.envs[h].play()
                    except Exception:
                        pass

        print(f"[Info] Creating structured rhythm with bass and chord progression")
        self.pat = Pattern(function=rhythm, time=beat).play()
        print(f"[Info] Rhythm pattern created with bass on beats 1 & 3")

        # Melody with constrained motion and rests for structure
        melody_pos = random.randint(0, len(scale)-1)
        melody_count = [0]
        melody_direction = [1]
        phrase_counter = [0]
        chord_prog_idx = [0]
        beat_counter = [0]
        
        def melody():
            melody_count[0] += 1
            beat_counter[0] += 1
            if melody_count[0] == 1:
                print(f"[Info] Melody pattern started with structure")
            
            nonlocal melody_pos
            if not self.oscillators or not self.envs:
                return
            
            phrase_counter[0] += 1
            
            # Get current chord for constraint
            current_chord_degree = chord_prog[(chord_prog_idx[0] // 4) % len(chord_prog)]
            current_chord = chord_from_scale(scale, current_chord_degree, oct_shift=0)
            
            # Update chord index every 4 beats
            if beat_counter[0] % 4 == 0:
                chord_prog_idx[0] = beat_counter[0]
            
            # Add rests: every 8 beats, rest for 1 beat to break up the melody
            if phrase_counter[0] % 8 == 0:
                return  # Rest beat - don't play melody
            
            # Change direction every 6-10 notes for phrasing
            if phrase_counter[0] % random.randint(6, 10) == 0:
                melody_direction[0] *= -1
            
            # Mostly stepwise motion (1 step), occasionally 2 steps
            step_size = random.choice([1, 1, 1, 2])
            new_pos = melody_pos + (step_size * melody_direction[0])
            
            # Constrain to scale
            if new_pos < 0:
                melody_pos = 1
                melody_direction[0] = 1
            elif new_pos >= len(scale):
                melody_pos = len(scale) - 2
                melody_direction[0] = -1
            else:
                melody_pos = new_pos
            
            # Prefer chord tones, but allow passing tones
            note = scale[melody_pos]
            if random.random() < 0.8:  # 80% chance to favor chord tone
                note = random.choice(current_chord)
            
            # Octave variation: mostly stay in range, jump up occasionally
            if phrase_counter[0] % 10 == 0:
                note += 12  # Jump up every 10 notes
            elif phrase_counter[0] % 7 == 0 and phrase_counter[0] > 2:
                note -= 12  # Jump down occasionally
            
            freq = mtof(note)
            
            if not self.oscillators:
                return
            
            # Rotate through lead voices for variation
            lead = (melody_count[0] // 2) % len(self.oscillators)
            if lead >= len(self.oscillators):
                return
            
            try:
                osc = self.oscillators[lead]
                if hasattr(osc, "freq"):
                    osc.freq = freq
                self.envs[lead].play()
            except Exception:
                pass

        self.mel_pat = Pattern(function=melody, time=beat*0.5).play()

        # Drum machine
        def drum_step():
            k = Sine(freq=60, mul=0.8).mix(1)
            kenv = Adsr(0.001, 0.03, 0.0, 0.05, mul=0.9)
            kick = ButLP(k * kenv, freq=120).out()
            kenv.play()
            s = Noise(mul=0.6)
            senv = Adsr(0.001, 0.02, 0.0, 0.08, mul=0.7)
            sna = ButBP(s * senv, freq=1800, q=0.6).out()
            senv.play()
            h = Noise(mul=0.3)
            henv = Adsr(0.001, 0.01, 0.0, 0.02, mul=0.4)
            hh = ButHP(h * henv, freq=6000).out()
            henv.play()

        if drums_on:
            self.drum_pat = Pattern(function=drum_step, time=beat).play()
        else:
            self.drum_pat = None

        if gui_callback:
            gui_callback(f"Playing {length}s at {tempo} BPM — recording to {export_file}")

        try:
            time.sleep(length)
        finally:
            try:
                if self.pat: self.pat.stop()
                if self.mel_pat: self.mel_pat.stop()
                if self.drum_pat: self.drum_pat.stop()
            except Exception:
                pass
            try:
                fade = Fader(fadein=0.01, fadeout=0.5, dur=0.6).play()
                time.sleep(0.6)
            except Exception:
                pass
            self.stop_server()
            self.is_running = False
            if gui_callback:
                gui_callback(f"Finished — saved {export_file}")

# ---------------- GUI ----------------
class FullGUI:
    def __init__(self):
        self.synth = BenSynth()
        self.root = tk.Tk()
        self.root.title("Ben's Synth — Presets & Queue")
        self.root.geometry("800x600")

        # top controls
        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=8, pady=6)
        ttk.Label(top, text="7-stellige Zahl:").pack(side="left")
        self.code_entry = ttk.Entry(top, width=16, font=("Consolas", 12))
        self.code_entry.pack(side="left", padx=6)
        self.random_btn = ttk.Button(top, text="Random", command=self.set_random)
        self.random_btn.pack(side="left")

        # middle: left control panel, right queue
        body = ttk.Frame(self.root)
        body.pack(fill="both", expand=True, padx=8, pady=4)

        left = ttk.Frame(body)
        left.pack(side="left", fill="y", padx=(0,8))

        # scale & preset
        ttk.Label(left, text="Skala:").pack(anchor="w")
        self.scale_var = tk.StringVar(value="Major")
        self.scale_box = ttk.Combobox(left, textvariable=self.scale_var, values=list(SCALES.keys()), state="readonly", width=16)
        self.scale_box.pack(anchor="w", pady=2)

        ttk.Label(left, text="Preset:").pack(anchor="w", pady=(8,0))
        self.preset_var = tk.StringVar(value="Pad")
        self.preset_box = ttk.Combobox(left, textvariable=self.preset_var, values=self.load_preset_names(), state="readonly", width=18)
        self.preset_box.pack(anchor="w", pady=2)

        # preset editor
        ps_frame = ttk.Frame(left)
        ps_frame.pack(anchor="w", pady=(8,2))
        ttk.Button(ps_frame, text="Save Preset...", command=self.save_preset_dialog).pack(side="left", padx=2)
        ttk.Button(ps_frame, text="Delete Preset", command=self.delete_preset).pack(side="left", padx=2)

        # tempo / length
        ttk.Label(left, text="Tempo (BPM):").pack(anchor="w", pady=(8,0))
        self.tempo_entry = ttk.Entry(left, width=10)
        self.tempo_entry.pack(anchor="w", pady=2)
        ttk.Label(left, text="Länge (s, optional):").pack(anchor="w", pady=(6,0))
        self.length_entry = ttk.Entry(left, width=10)
        self.length_entry.pack(anchor="w", pady=2)

        # toggles
        self.gb_var = tk.BooleanVar(value=False)
        self.drum_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left, text="Gameboy Mode", variable=self.gb_var).pack(anchor="w", pady=4)
        ttk.Checkbutton(left, text="Drums", variable=self.drum_var).pack(anchor="w", pady=2)

        # effects sliders
        ttk.Label(left, text="Reverb:").pack(anchor="w", pady=(8,0))
        self.rev_scale = ttk.Scale(left, from_=0.0, to=0.95, value=0.4, orient="horizontal", length=160)
        self.rev_scale.pack(anchor="w")
        ttk.Label(left, text="Delay:").pack(anchor="w", pady=(6,0))
        self.dly_scale = ttk.Scale(left, from_=0.0, to=0.95, value=0.2, orient="horizontal", length=160)
        self.dly_scale.pack(anchor="w")
        ttk.Label(left, text="Bitcrush:").pack(anchor="w", pady=(6,0))
        self.bit_scale = ttk.Scale(left, from_=0.0, to=1.0, value=0.0, orient="horizontal", length=160)
        self.bit_scale.pack(anchor="w")

        # filename & controls
        ttk.Label(left, text="Export filename:").pack(anchor="w", pady=(8,0))
        self.filename_entry = ttk.Entry(left, width=24)
        self.filename_entry.insert(0, "out.wav")
        self.filename_entry.pack(anchor="w", pady=2)

        btns = ttk.Frame(left)
        btns.pack(anchor="w", pady=8)
        ttk.Button(btns, text="Start (Play & Record)", command=self.on_start).pack(side="left", padx=2)
        ttk.Button(btns, text="Stop", command=self.on_stop).pack(side="left", padx=2)
        ttk.Button(btns, text="Show Scope", command=self.show_scope).pack(side="left", padx=2)

        # right: queue and status
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

        # bottom status
        self.status_var = tk.StringVar(value="Audio engine initializing in background...")
        ttk.Label(self.root, textvariable=self.status_var).pack(fill="x", pady=(6,4))

        # demo presets quick menu
        demo = ttk.Frame(self.root)
        demo.pack(fill="x", padx=8)
        ttk.Label(demo, text="Demo Presets:").pack(side="left")
        self.demo_box = ttk.Combobox(demo, values=list(DEFAULT_PRESETS.keys()), state="readonly")
        self.demo_box.pack(side="left", padx=6)
        ttk.Button(demo, text="Apply Demo", command=self.apply_demo).pack(side="left")
        
        # Monitor background init and update status when ready
        self.root.after(100, self._check_server_ready)

    # ---------- Preset file helpers ----------
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
        # build preset from current controls
        preset = {
            "attack": float(0.1),
            "decay": float(0.3),
            "sustain": float(0.7),
            "release": float(0.5),
            "mul": float(0.5)
        }
        # attempt to derive values from currently selected preset (if any)
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

    # ---------- Queue helpers ----------
    def add_current_to_queue(self):
        user = self.code_entry.get().strip()
        if user == "":
            user = str(random.randint(1000000, 9999999))
            self.code_entry.delete(0, tk.END)
            self.code_entry.insert(0, user)
        # simple validation
        try:
            v = int(user)
            self.queue_list.insert(tk.END, str(v))
            self.update_status(f"Added {v} to queue")
        except Exception:
            self.update_status("Invalid number — must be integer")

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
        # confirm
        if not messagebox.askyesno("Render Queue", f"Render {len(items)} items sequentially? This will record each to separate files."):
            return
        def worker():
            for idx, it in enumerate(items):
                code = int(it)
                outname = f"{os.path.splitext(fname_base)[0]}_{idx+1}.wav"
                self.update_status(f"Rendering {it} -> {outname}")
                # collect current UI settings to pass
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

    # ---------- Actions ----------
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
        return { 'scale': scale_name, 'preset': preset, 'tempo': tempo, 'length': length, 'gb': gb, 'drums': drums, 'rev': rev, 'dly': dly, 'bit': bit }

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
        #Monitor background server initialization and update status#
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
        # naive apply: set preset combobox to name if it exists
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
