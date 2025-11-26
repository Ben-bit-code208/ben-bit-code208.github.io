import pygame

pygame.mixer.init()

class SoundManager:
    def __init__(self):
        self.current_music = None

    def play_music(self, file, loop=True):
        if self.current_music != file:  # Nur wechseln, wenn nötig
            pygame.mixer.music.stop()
            pygame.mixer.music.load(file)
            pygame.mixer.music.play(-1 if loop else 0)
            self.current_music = file

    def stop_music(self):
        pygame.mixer.music.stop()
        self.current_music = None

    def play_sound(self, file):
        """Einmaliger Soundeffekt (z. B. Klick, Treffer, Explosion)."""
        sound = pygame.mixer.Sound(file)
        sound.play()
