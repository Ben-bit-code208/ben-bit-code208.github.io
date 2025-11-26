import os
import sys
import subprocess
import importlib
import inspect


    

try:
    # import pygame dynamically to avoid static-analyzer unresolved-import warnings
    pygame = importlib.import_module("pygame")
    Rect = getattr(pygame, "Rect")
except Exception:
    print("Error: the 'pygame' library is required but not installed.\nInstall it with: pip install pygame")
    sys.exit(1)
from tkinter import Tk, filedialog
# matrix.py
# Main menu program that launches a game from "irgendwas.py" (or "irgenwas.py")
# - Uses a background picture for the main menu
# - Lets you pick a picture to pass as the "guess field" background for the other module
# - Tries to call common entry functions in the imported module; falls back to running the module as a subprocess
#
# Put this file next to your irgendwas.py (or irgenwas.py). Provide "menu_bg.png" (or change the path below).


# Configuration: change these names/paths if you want
MENU_BG = os.path.join(os.path.dirname(__file__), "menu_bg.png")  # main menu background image
WINDOW_SIZE = (900, 600)
WINDOW_TITLE = "Cool Menu — Launch irgendwas"

pygame.init()
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption(WINDOW_TITLE)
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("arial", 28)
BIG_FONT = pygame.font.SysFont("arial", 46)

def load_image(path, size=None):
    if not path or not os.path.isfile(path):
        return None
    img = pygame.image.load(path).convert_alpha()
    if size:
        img = pygame.transform.smoothscale(img, size)
    return img

class Button:
    def __init__(self, rect, text, bg=(30, 30, 30), fg=(255,255,255)):
        self.rect = Rect(rect)
        self.text = text
        self.bg = bg
        self.fg = fg
        self.hover = False
    def draw(self, surf):
        color = tuple(min(255, c + (30 if self.hover else 0)) for c in self.bg)
        pygame.draw.rect(surf, color, self.rect, border_radius=10)
        txt = FONT.render(self.text, True, self.fg)
        tw, th = txt.get_size()
        surf.blit(txt, (self.rect.centerx - tw//2, self.rect.centery - th//2))
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

def choose_image_file():
    # simple file picker using tkinter
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    file = filedialog.askopenfilename(
        title="Select guess-field background image",
        filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("All files", "*.*")]
    )
    root.destroy()
    return file or None

def find_local_module_file(names=("irgendwas.py", "irgenwas.py")):
    base = os.path.dirname(__file__)
    for n in names:
        p = os.path.join(base, n)
        if os.path.isfile(p):
            return p
    return None

def launch_irgendwas(guess_bg_path=None):
    """
    Attempts to run the other module in-process:
      - imports module (irgendwas or irgenwas)
      - tries common function names (play, main, run, start_game, run_game, play_game)
      - if function accepts a parameter, passes guess_bg_path
    If import/call fails, falls back to launching the module as a subprocess with --guess-bg argument.
    """
    module_names = ["irgendwas", "irgenwas"]
    entry_names = ["play", "main", "run", "start_game", "run_game", "play_game"]
    # First try to import
    for modname in module_names:
        try:
            if modname in sys.modules:
                mod = importlib.reload(sys.modules[modname])
            else:
                mod = importlib.import_module(modname)
        except Exception:
            continue
        # try to find callable
        for name in entry_names:
            fn = getattr(mod, name, None)
            if callable(fn):
                sig = None
                try:
                    sig = inspect.signature(fn)
                except Exception:
                    pass
                # If function accepts parameters, pass guess_bg_path
                try:
                    if sig and len(sig.parameters) >= 1:
                        # Many functions might expect path or surface; pass path first
                        return fn(guess_bg_path)
                    else:
                        return fn()
                except TypeError:
                    # fallback: try without args
                    try:
                        return fn()
                    except Exception as e:
                        raise
        # if no known entry, but module has a __main__ logic, try to call module.main() similarly
        if hasattr(mod, "__dict__") and "main" in mod.__dict__ and callable(mod.__dict__["main"]):
            try:
                return mod.__dict__["main"](guess_bg_path) if guess_bg_path else mod.__dict__["main"]()
            except Exception:
                pass
    # If import attempts failed, fallback to running the file as a subprocess
    local_file = find_local_module_file(module_names)
    if local_file:
        args = [sys.executable, local_file]
        if guess_bg_path:
            args += ["--guess-bg", guess_bg_path]
        # Before launching subprocess, quit pygame display to release window if needed
        pygame.display.quit()
        try:
            subprocess.run(args)
        finally:
            # re-init pygame display so program can continue if subprocess returns
            pygame.display.init()
            pygame.display.set_mode(WINDOW_SIZE)
    else:
        raise FileNotFoundError("Could not find irgendwas.py or irgenwas.py next to matrix.py")

def draw_title_and_footer(surf, title, footer):
    t = BIG_FONT.render(title, True, (230,230,230))
    surf.blit(t, (40, 30))
    f = FONT.render(footer, True, (200,200,200))
    surf.blit(f, (40, WINDOW_SIZE[1] - 40))

def main():
    menu_bg_img = load_image(MENU_BG, WINDOW_SIZE)
    guess_bg = None  # path to image for guess field in the other module
    # Buttons
    btn_play = Button((WINDOW_SIZE[0]//2 - 140, 200, 280, 64), "Play Irgendwas", bg=(10,120,180))
    btn_choose = Button((WINDOW_SIZE[0]//2 - 140, 290, 280, 64), "Choose Guess Background", bg=(20,100,60))
    btn_quit = Button((WINDOW_SIZE[0]//2 - 140, 380, 280, 64), "Quit", bg=(160,40,40))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if btn_play.handle_event(event):
                try:
                    # Launch the other module. This may block until that game ends.
                    launch_irgendwas(guess_bg)
                except Exception as e:
                    print("Error launching other module:", e)
                # re-load display surface after returned
                screen.fill((0,0,0))
            if btn_choose.handle_event(event):
                chosen = choose_image_file()
                if chosen:
                    guess_bg = chosen
            if btn_quit.handle_event(event):
                running = False

        # draw background
        if menu_bg_img:
            screen.blit(menu_bg_img, (0,0))
        else:
            screen.fill((12,12,30))
            # subtle animated stars
            for i in range(40):
                pygame.draw.circle(screen, (20,20,60), ((i*37) % WINDOW_SIZE[0], (i*23+i*7) % WINDOW_SIZE[1]), 1)

        # overlay panel
        panel = pygame.Surface((460, 360), pygame.SRCALPHA)
        panel.fill((10, 10, 10, 180))
        screen.blit(panel, (WINDOW_SIZE[0]//2 - 230, 140))

        draw_title_and_footer(screen, "Matrix Menu", "Select Play to run irgendwas.py — pick an image for its guess-field")

        # show currently selected guess background
        gb_text = f"Guess BG: {os.path.basename(guess_bg) if guess_bg else 'None (default)'}"
        gb_render = FONT.render(gb_text, True, (200,200,200))
        screen.blit(gb_render, (WINDOW_SIZE[0]//2 - 200, 170))

        # draw buttons
        for b in (btn_play, btn_choose, btn_quit):
            b.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()