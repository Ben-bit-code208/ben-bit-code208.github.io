global start_game
global start_test_mode
global ensure_vlc
global btn_videotest
global btn_audiotest
global vlc
from encodings.punycode import T
import os
import sys
import time
import random
import hashlib
import threading
import subprocess
import ctypes
import gettinghacked
from datetime import datetime
from http.cookiejar import LoadError
import tkinter as tk
from tkinter import messagebox, simpledialog
import soundengine
from tracemalloc import start
from unittest import loader
from webbrowser import get
import download_helper
import vlc
global get_direct_stream
global FullscreenPlayer
global YOUTUBE_URL
ensure_vlc = None
from yt_dlp import YoutubeDL
global btn_exittest
get_direct_stream = None
def setup_debug_log():
    """Set up debug logging to a file and return a print function."""
    log_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'debug_log.txt')
    
    def debug_print(message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}\n"
        try:
            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(log_message)
        except Exception:
            pass  # Fail silently if logging fails
    
    return debug_print

# Initialize debug logging
debug_print = setup_debug_log()
debug_print("=== Starting application ===")

# Global variables
CORRECT_PASSWORD_HASH = hashlib.sha256('Ben2013'.encode()).hexdigest()
balu_wake_counter = 0
pass_counter = 0
not_checked = 1
loaderror = 0
TEST_MODE_ACTIVE = False
TEST_SNAPSHOT = None
DOWNLOAD_EVENT = threading.Event()
use_internet = False
INTERNET_PROMPTED = False
DOWNLOAD_TRIED = False
DOWNLOAD_SUCCESS = False
DOWNLOAD_PATH = None

# Game state variables
root = None
ask = None
game_window = None
text_output = None
entry = None
btn_game = None
balu_prob_scale = None
balu_frame = None
balu_frame_label = None
balu_prob_value_label = None
found_icon = None

# Game settings
easy = 0
medium = 0
hard = 0
hardcore = 0
random_mode = 0
impossible_mode = 0
difficulty_asked = False
BALU_PROBABILITY = 0.7
current_random_number = None

def initialize_main_window():
    """Initialize and configure the main window."""
    global root
    debug_print("Creating main window")
    root = tk.Tk()
    root.title('Main Menü')
    root.geometry('1920x1080')
    root.configure(bg='#FFFFFF')
    root.resizable(False, False)
    root.withdraw()  # Hide initially
    
    # Set up icon
    icon_candidates = ['icon.ico', os.path.join('DATA', 'icon.ico'), os.path.join('..', 'icon.ico')]
    for ic in icon_candidates:
        try_path = os.path.abspath(ic)
        if os.path.exists(try_path):
            try:
                root.iconbitmap(try_path)
                debug_print(f"Set icon: {try_path}")
                break
            except Exception as e:
                debug_print(f"Failed to set icon {try_path}: {e}")
    
    return root



def difficulty_selection():
    """Create and show the difficulty selection window."""
    debug_print("\n=== Difficulty Selection Debug ===")
    global not_checked, loaderror, root, ask
    
    try:
        debug_print(f"Starting difficulty_selection: not_checked={not_checked}, loaderror={loaderror}")
        if not_checked == 1 and not loaderror == 1:
            debug_print("Creating difficulty window...")
            
            # Ensure any existing window is cleaned up
            if hasattr(ask, 'winfo_exists') and ask is not None and ask.winfo_exists():
                try:
                    ask.destroy()
                except Exception as e:
                    debug_print(f"Error destroying existing window: {e}")
            
            # Create new window
            ask = tk.Toplevel(root)
            ask.title('Schwierigkeit')
            ask.configure(bg='#FFFFFF')
            ask.resizable(False, False)
            
            # Center window
            screen_width = ask.winfo_screenwidth()
            screen_height = ask.winfo_screenheight()
            x = (screen_width - 854) // 2
            y = (screen_height - 480) // 2
            ask.geometry(f"854x480+{x}+{y}")
            
            # Create layout container
            container = tk.Frame(ask, bg='#FFFFFF')
            container.pack(expand=True, fill='both', padx=20, pady=20)
            
            # Create UI elements
            label = tk.Label(container, text='Welche Schwierigkeit willst du?',
                           bg='#FFFFFF', fg='#000000',
                           font=('Segoe UI', 14, 'bold'))
            label.pack(pady=24)
            
            for diff, text in [('easy', 'Easy'), ('medium', 'Medium'), 
                             ('hard', 'Hard'), ('hardcore', 'Hardcore'),
                             ('random', 'Random'), ('impossible', 'Impossible')]:
                btn = tk.Button(container, text=text,
                              bg='#FFFFFF', fg='#000000',
                              font=('Segoe UI', 12),
                              width=20, 
                              command=lambda d=diff: update_difficulty(d))
                btn.pack(pady=12)
            
            # Hide main window
            root.withdraw()
            
            # Focus new window
            ask.focus_force()
            debug_print("Difficulty selection window created and configured")
            
            not_checked = 0
            loaderror = 0
            
    except Exception as e:
        debug_print(f"Error in difficulty_selection: {e}")
        loaderror = 1
        not_checked = 1
        import traceback
        traceback.print_exc()

def update_difficulty(difficulty):
    """Update game difficulty settings."""
    global easy, medium, hard, hardcore, random_mode, impossible_mode, difficulty_asked, BALU_PROBABILITY, ask
    debug_print(f"Updating difficulty to: {difficulty}")
    
    # Reset difficulties
    easy = medium = hard = hardcore = 0
    
    # Set chosen difficulty
    if difficulty == 'easy':
        easy = 1
        BALU_PROBABILITY = random.randint(60, 90) / 100.0
    elif difficulty == 'medium':
        medium = 1
        BALU_PROBABILITY = random.randint(40, 70) / 100.0
    elif difficulty == 'hard':
        hard = 1
        BALU_PROBABILITY = random.randint(20, 50) / 100.0
    elif difficulty == 'hardcore':
        hardcore = 1
        BALU_PROBABILITY = 0.0
    elif difficulty == 'random_mode':
        choice = random.choice(['easy', 'medium', 'hard', 'hardcore', 'impossible_mode', 'random_mode'])
        debug_print(f"Randomly selected difficulty: {choice}")
        update_difficulty(choice)
        return
    
    difficulty_asked = True
    debug_print(f"Set difficulty: {difficulty} (easy={easy}, medium={medium}, hard={hard}, hardcore={hardcore} random_mode={random_mode}, impossible_mode={impossible_mode})")
    
    # Window management
    try:
        if ask and ask.winfo_exists():
            ask.destroy()
        if root and root.winfo_exists():
            root.deiconify()
            root.update()
    except Exception as e:
        debug_print(f"Error in window management: {e}")
    
    # Start game after brief delay
    root.after(100, start_game)

def start_game():
    """Initialize and start the game window."""
    global game_window, entry, text_output
    global balu_prob_scale, balu_frame
    global balu_frame_label, balu_prob_value_label
    
    debug_print(f"Starting game with difficulty: easy={easy}, medium={medium}, hard={hard}, hardcore={hardcore} random_mode={random_mode}, impossible_mode={impossible_mode}")
    
    # Überprüfe, ob die Schwierigkeit ausgewählt wurde
    if not (easy == 1 or medium == 1 or hard == 1 or hardcore == 1 or random_mode == 1 or impossible_mode == 1):
        debug_print("No difficulty selected, showing selection window")
        parent = root if 'root' in globals() and root.winfo_exists() else None
        messagebox.showwarning("Keine Schwierigkeit", "Bitte wähle zuerst eine Schwierigkeit!", parent=parent)
        difficulty_selection()
        return
    
    # Cleanup existing game window
    try:
        if 'game_window' in globals() and game_window is not None and game_window.winfo_exists():
            game_window.destroy()
    except Exception as e:
        debug_print(f"Error cleaning up old game window: {e}")
    
    # Hide main menu
    try:
        if root and root.winfo_exists():
            root.withdraw()
    except Exception as e:
        debug_print(f"Error hiding main window: {e}")
    
    # Create new game window
    debug_print("Creating game window")
    game_window = tk.Toplevel(root)
    game_window.title('Mr.X Game')
    game_window.configure(bg='#FFFFFF')
    game_window.geometry('1920x1080')
    
    # Set icon if available
    try:
        if 'found_icon' in globals() and found_icon:
            game_window.iconbitmap(found_icon)
    except Exception as e:
        debug_print(f"Error setting game window icon: {e}")
    
    # Disable start button while game is running
    if btn_game:
        btn_game.config(state=tk.DISABLED)
    
    # Set up window close handler
    def _on_game_close():
        try:
            game_window.destroy()
        except Exception:
            pass
        try:
            if btn_game:
                btn_game.config(state=tk.NORMAL)
        except Exception:
            pass
        try:
            if root and root.winfo_exists():
                root.deiconify()
        except Exception:
            pass
    
    game_window.protocol('WM_DELETE_WINDOW', _on_game_close)
    
    # Create Balu probability frame (for test mode)
    balu_frame = tk.Frame(game_window, bg='#FFFFFF', bd=3, relief=tk.RIDGE, height=120)
    balu_frame_label = tk.Label(balu_frame, text='Balu appear chance (%)',
                               font=('Segoe UI', 12, 'bold'),
                               bg='#FFFFFF', fg='#000000')
    
    balu_prob_scale = tk.Scale(balu_frame, from_=0, to=100,
                              orient=tk.HORIZONTAL, length=560,
                              bg='#FFFFFF', fg='#000000',
                              font=('Segoe UI', 14),
                              showvalue=False)
    balu_prob_scale.set(int(BALU_PROBABILITY * 100))
    
    balu_prob_value_label = tk.Label(balu_frame,
                                    text=f'{int(BALU_PROBABILITY * 100)}%',
                                    font=('Segoe UI', 13, 'bold'),
                                    bg='#FFFFFF', fg='#000000')
    
    balu_prob_scale.config(command=lambda v: balu_prob_value_label.config(text=f'{int(float(v))}%'))
    
    # Show Balu frame if in test mode
    try:
        if TEST_MODE_ACTIVE:
            balu_frame.pack(pady=8, fill='x', padx=10)
            balu_frame_label.pack(anchor='w', padx=10, pady=(8, 0))
            balu_prob_scale.pack(padx=10, pady=(6, 4), fill='x')
            balu_prob_value_label.pack(anchor='e', padx=10, pady=(0, 8))
    except Exception as e:
        debug_print(f"Error setting up Balu frame: {e}")
    
    # Create main game elements
    text_output = tk.Text(game_window, height=10, width=70,
                         bg='#FFFFFF', fg='#000000',
                         insertbackground='#FFFFFF',
                         font=('', 12))
    text_output.pack(pady=6, fill='both', expand=True)
    
    entry = tk.Entry(game_window, width=60,
                    bg='#ffffff', fg='#000000',
                    font=('Segoe UI', 12))
    entry.pack(pady=(4,2))
    entry.bind('<Return>', lambda event: run_command())
    
    button_exec = tk.Button(game_window, text='Guess',
                           command=run_command,
                           bg='#ffffff', fg='#000000',
                           font=('Segoe UI', 10))
    button_exec.pack(pady=8)
    
    # Initialize game state
    initialize_game()
    
    debug_print("Game window created and initialized")

def initialize_game():
    """Initialize or restart the game."""
    global current_random_number, text_output
    debug_print("Initializing game")
    
    # Set random number based on difficulty
    try:
        if globals().get('easy', 0) == 1:
            current_random_number = random.randint(1, 50)
            range_text = "between 1 and 50"
        elif globals().get('medium', 0) == 1:
            current_random_number = random.randint(1, 100)
            range_text = "between 1 and 100"
        elif globals().get('hard', 0) == 1:
            current_random_number = random.randint(1, 1000)
            range_text = "between 1 and 1000"
        elif globals().get('hardcore', 0) == 1:
            current_random_number = random.randint(1, 10000)
            range_text = "between 1 and 10000"
        elif globals().get('impossible_mode', 0) == 1:
            current_random_number = random.randint(1, 10000000)
            range_text = "between 1 and 10000000"
        else:
            current_random_number = random.randint(1, 100)
            range_text = "between 1 and 100"
        debug_print(f"Set random number {current_random_number} {range_text}")
    except Exception as e:
        debug_print(f"Error setting random number: {e}")
        current_random_number = random.randint(1, 100)
        range_text = "between 1 and 100"
    
    messagebox.showinfo('Game Started', f'Guess the random number {range_text}!')
    
    # Initialize text output
    try:
        if 'text_output' in globals() and text_output and text_output.winfo_exists():
            text_output.delete('1.0', tk.END)
            welcome_text = (
                f"Welcome to the game!\n"
                f"Guess a number {range_text}.\n"
                "Type 'help' for available commands.\n"
                "Good luck!\n\n"
            )
            text_output.insert('1.0', welcome_text)
            text_output.see(tk.END)
            debug_print("Text output initialized")
    except Exception as e:
        debug_print(f"Error initializing text output: {e}")

def run_command():
    """Process user commands."""
    global balu_wake_counter, pass_counter, current_random_number
    
    cmd = entry.get().strip().lower()
    output = ''
    debug_print(f"Processing command: {cmd}")
    
    if cmd == 'clear':
        text_output.delete('1.0', tk.END)
    elif cmd == 'help':
        output = 'Available Commands:\n- clear: clear screen\n- help: show commands\n- restart: restart game\n- exit: close game\n- balu: interact with Balu\n- [number]: make a guess'
    elif cmd == 'restart':
        initialize_game()
    elif cmd == 'exit':
        try:
            if 'game_window' in globals() and game_window and game_window.winfo_exists():
                game_window.destroy()
        except Exception as e:
            debug_print(f"Error closing game window: {e}")
    elif cmd == 'balu':
        # Get Balu probability
        try:
            runtime_prob = BALU_PROBABILITY
            if 'balu_prob_scale' in globals() and balu_prob_scale:
                runtime_prob = float(balu_prob_scale.get()) / 100.0
        except Exception:
            runtime_prob = BALU_PROBABILITY
        
        # Handle Balu appearance
        if random.random() < runtime_prob:
            if globals().get('easy', 0) == 1:
             random_number2 = random.randint(1, 50)
             range_text = "between 1 and 50"
            elif globals().get('medium', 0) == 1:
             random_number2 = random.randint(1, 100)
             range_text = "between 1 and 100"
            elif globals().get('hard', 0) == 1:
             random_number2 = random.randint(1, 1000)
             range_text = "between 1 and 1000"
            elif globals().get('hardcore', 0) == 1:
             random_number2 = random.randint(1, 10000)
             range_text = "between 1 and 10000"
            elif globals().get('impossible_mode', 0) == 1:
             current_random_number = random.randint(1, 10000000)
             output = ' /\\_/\\ \n( o.o )  Meow!\n > ^ <\n'
             output += f"Balu's number: {random_number2}\n"
            if random_number2 < current_random_number:
                output += 'Result: - (Balu < Current)'
            elif random_number2 > current_random_number:
                output += 'Result: + (Balu > Current)'
            else:
                output += 'Result: = (Equal)'
            debug_print(f"Balu appeared with number {random_number2}")
        else:
            balu_wake_counter += 1
            if balu_wake_counter >= 3:
                output += 'Balu chose the new number between {range_text}!\n'
                if random.random() < runtime_prob:
                 if globals().get('easy', 0) == 1:
                  random_number2 = random.randint(1, 50)
                  range_text = "between 1 and 50"
                 elif globals().get('medium', 0) == 1:
                  random_number2 = random.randint(1, 100)
                  range_text = "between 1 and 100"
                 elif globals().get('hard', 0) == 1:
                  random_number2 = random.randint(1, 1000)
                  range_text = "between 1 and 1000"
                 elif globals().get('hardcore', 0) == 1:
                  random_number2 = random.randint(1, 10000)
                  range_text = "between 1 and 10000"
                 elif globals().get('impossible_mode', 0) == 1:
                  current_random_number = random.randint(1, 10000000)
                  balu_wake_counter = 0
            else:
                output = f'Balu is sleeping, try again later. Wake attempts: {balu_wake_counter}/3'
                debug_print(f"Balu sleeping, attempts: {balu_wake_counter}")
    elif cmd.isdigit():
        guess = int(cmd)
        if guess == current_random_number:
            output = 'You guessed the random number!'
            debug_print("Player won!")
            play_again = messagebox.askyesno('Play Again?', 'Do you want to play again?')
            if play_again:
                initialize_game()
            else:
                if 'game_window' in globals() and game_window and game_window.winfo_exists():
                    game_window.destroy()
        
        elif guess < current_random_number:
            output = 'Too low! Try again.'
        else:
            output = 'Too high! Try again.'
    elif cmd == 'video test':
        gettinghacked.runhack()
    elif cmd == 'audio test run':
        soundengine.SoundManager().play_sound('10.mp3')
    elif cmd == 'audio test stop':
        soundengine.SoundManager().stop_music()
    elif cmd == 'play sound':
        soundengine.SoundManager().play_sound('C:\\Windows\\Media\\chimes.wav')
    else:
        output = 'Unknown command or incorrect number.'
    
    # Update output
    if output:
        text_output.insert(tk.END, f'>>> {cmd}\n{output}\n\n')
        try:
            text_output.see(tk.END)
        except Exception:
            pass
    
    # Clear entry
    entry.delete(0, tk.END)

def exittest():
    """Exit test mode and reset related settings."""
    global TEST_MODE_ACTIVE, TEST_SNAPSHOT
    debug_print("Exiting test mode")
    
    TEST_MODE_ACTIVE = False
    TEST_SNAPSHOT = None
    
    # Hide test mode UI elements if game window exists
    try:
        if 'game_window' in globals() and game_window and game_window.winfo_exists():
            if 'balu_frame' in globals() and TEST_MODE_ACTIVE == True:
                balu_frame.pack_forget()
                balu_frame_label.pack_forget()
                balu_prob_scale.pack_forget()
                balu_prob_value_label.pack_forget()
                btn_exittest.pack_forget()
                btn_videotest.pack_forget()
                btn_audiotest.pack_forget()
    except Exception as e:
        debug_print(f"Error hiding test mode UI: {e}")
    
    messagebox.showinfo('Test Mode', 'Test mode deactivated.')
def start_test_mode():
    """Start test mode after password verification."""
    global pass_counter, current_random_number, TEST_MODE_ACTIVE, TEST_SNAPSHOT
    debug_print("Test mode requested")
    
    
    password = simpledialog.askstring('Test Mode', 'Enter password:', show='*', parent=root)
    if password == 'Ben2013.':
        debug_print("Test mode password correct")
        try:
            _ = current_random_number
        except NameError:
            if easy == 1:
                current_random_number = random.randint(1, 50)
            elif medium == 1:
                current_random_number = random.randint(1, 100)
            elif hard == 1:
                current_random_number = random.randint(1, 1000)
            elif hardcore == 1:
                current_random_number = random.randint(1, 10000)
            elif impossible_mode == 1:
                current_random_number = random.randint(1, 10000000)
            else:
                current_random_number = random.randint(1, 100)
                debug_print(f"Set initial random number: {current_random_number}")
        
        if TEST_SNAPSHOT is None:
            TEST_SNAPSHOT = current_random_number
            debug_print(f"Created test snapshot: {TEST_SNAPSHOT}")
            
        messagebox.showinfo('Test Mode', f'Test mode activated! Random number is: {TEST_SNAPSHOT}')
        TEST_MODE_ACTIVE = True
        
        # Show test mode UI elements if game window exists
        try:
            if 'game_window' in globals() and game_window and game_window.winfo_exists():
                if 'balu_frame' in globals() and balu_frame:
                    balu_frame.pack(pady=8, fill='x', padx=10)
                    balu_frame_label.pack(anchor='w', padx=10, pady=(8, 0))
                    balu_prob_scale.pack(padx=10, pady=(6, 4), fill='x')
                    balu_prob_value_label.pack(anchor='e', padx=10, pady=(0, 8))
                        #testmode buttons
                    btn_exittest = tk.Button(root, text='❌ Exit test mode',
                            command=lambda: exittest(), font=('Segoe UI', 12),
                            bg='white', fg='#000000')
                    btn_videotest = tk.Button(root, text='📺 Video Test',
                            command=lambda: gettinghacked.runhack, font=('Segoe UI', 12),
                            bg='white', fg='#000000')
                    btn_audiotest = tk.Button(root, text='🔊 Audio Test',
                              command=lambda: soundengine.SoundManager().play_sound('\\10.mp3'), font=('Segoe UI', 12),
                              bg='white', fg='#000000')
                    btn_exittest.pack(pady=8, fill='x', padx=60)
                    btn_videotest.pack(pady=8, fill='x', padx=60)
                    btn_audiotest.pack(pady=8, fill='x', padx=60)
                    
        except Exception as e:
            debug_print(f"Error showing test mode UI: {e}")
            
    else:
        debug_print("Wrong test mode password")
        pass_counter += 1
        messagebox.showwarning('Wrong password', 'Wrong password.')
        if pass_counter >= 3:
            debug_print("Too many wrong password attempts")
            messagebox.showerror('you haked', 'you haked')
            gettinghacked.runhack()


def create_main_menu():
    """Create the main menu buttons and UI elements."""
    global btn_game, label
    debug_print("Creating main menu")
    
    label = tk.Label(root, text='Welcome! Choose an option:', 
                    font=('Segoe UI', 14), bg='#FFFFFF', fg='#000000')
    label.pack(pady=24)
    
    btn_game = tk.Button(root, text='🎮  Start MR.X', 
                        command=start_game, font=('Segoe UI', 12),
                        bg='white', fg='#000000')
    btn_game.pack(pady=8, fill='x', padx=60)
    
    btn_testmode = tk.Button(root, text='🔒 Test Mode',
                            command=start_test_mode, font=('Segoe UI', 12),
                            bg='white', fg='#000000')
    btn_testmode.pack(pady=8, fill='x', padx=60)
    if TEST_MODE_ACTIVE == True:
     btn_exittest = tk.Button(root, text='❌ Exit test mode',
                            command=lambda: exittest(), font=('Segoe UI', 12),
                            bg='white', fg='#000000')
     btn_videotest = tk.Button(root, text='📺 Video Test',
                            command=lambda: gettinghacked.runhack, font=('Segoe UI', 12),
                            bg='white', fg='#000000')
     btn_audiotest = tk.Button(root, text='🔊 Audio Test',
                              command=lambda: soundengine.SoundManager().play_sound('\\10.mp3'), font=('Segoe UI', 12),
                              bg='white', fg='#000000')
                    
     btn_exittest.pack(pady=8, fill='x', padx=60)
     btn_videotest.pack(pady=8, fill='x', padx=60)
     btn_audiotest.pack(pady=8, fill='x', padx=60)
                    


    debug_print("Main menu created")

def main():
    """Main application entry point."""
    global root
    
    try:
        debug_print("Starting main application")
        
        # Initialize main window
        root = initialize_main_window()
        create_main_menu()
        
        # Schedule difficulty selection or show main window
        if not_checked == 1 and loaderror == 0:
            debug_print("Scheduling difficulty selection")
            root.after(100, difficulty_selection)
        else:
            debug_print("Showing main window directly")
            root.deiconify()
        
        # Start main loop
        debug_print("Starting main loop")
        root.mainloop()
        
    except Exception as e:
        debug_print(f"Fatal error in main application: {e}")
        import traceback
        traceback.print_exc()
    finally:
        debug_print("Application shutting down")
        # Cleanup
        try:
            if ask and hasattr(ask, 'winfo_exists') and ask.winfo_exists():
                ask.destroy()
        except Exception as e:
            debug_print(f"Error cleaning up ask window: {e}")
            
        try:
            if root and hasattr(root, 'winfo_exists') and root.winfo_exists():
                root.destroy()
        except Exception as e:
            debug_print(f"Error cleaning up root window: {e}")


if __name__ == '__main__':
    main()