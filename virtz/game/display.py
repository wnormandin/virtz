
import pygame


class DisplayManager:
    def __init__(self):
        pygame.init()

    @property
    def screen(self):
        return self._screen

    @screen.setter
    def screen(self, mode):
        resolution, fullscreen = mode
        if fullscreen:
            self._screen = pygame.display.set_mode(resolution, pygame.FULLSCREEN)
        else:
            self._screen = pygame.display.set_mode(resolution)
        pygame.display.set_caption('virtz')
