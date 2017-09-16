import pygame

class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos=(0, 0), frames=None):
        super(Sprite, self).__init__()
        self.image = frames[0][0]   # Only printing first frame for now
        self.rect = self.image.get_rect()
        self.pos = pos

    def _get_pos(self):
        return (self.rect.midbottom[0]-8)/16, (self.rect.midbottom[1]-8)/16

    def _set_pos(self):
        self.rect.midbottom = pos[0]*16+8, pos[1]*16+8
        self.depth = self.rect.midbottom[1]

    @property
    def pos(self):
        return self._get_pos, self._set_pos

    def move(self, dx, dy):
        self.rect.move_ip(dx, dy)
        self.depth = self.rect.midbottom[1]
