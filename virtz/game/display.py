
import pygame


class DisplayManager:
    def __init__(self):
        pygame.init()

    @property
    def screen(self):
        return self._screen

    @screen.setter
    def screen(self, mode):
        self._screen = pygame.display.set_mode(mode)
