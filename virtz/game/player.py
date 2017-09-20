import pygame
from pygame.locals import * # For keystrokes

class Player(pygame.sprite.Sprite):
    def __init__(self, img, pos=(0,0)):
        super().__init__()
        self.image = img
        self.image.convert_alpha()
        self.pos = pos
        self.rect = self.image.get_rect()

    def update(self, pressed_keys):
        if pressed_keys[K_UP]:
            self.rect.move_ip(0, -16)
        if pressed_keys[K_DOWN]:
            self.rect.move_ip(0, 16)
        if pressed_keys[K_LEFT]:
            self.rect.move_ip(-16, 0)
        if pressed_keys[K_RIGHT]:
            self.rect.move_ip(16, 0)
