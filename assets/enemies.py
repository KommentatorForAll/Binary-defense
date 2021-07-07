import arcade
import random
from typing import Dict, Optional

import main

SCALE = 4
ENEMY_SPREAD = 25


class Enemy(arcade.Sprite):

    def __init__(self, hp: int, speed: int, dmg: int, sprite: str, drops: dict,
                 enemy_names: Dict[str, "Enemy"], game: main.TowerDefenceMap):
        super().__init__(sprite, scale=SCALE)
        self.sprite = sprite
        self.hp = hp
        self.speed = speed
        self.dmg = dmg
        self.game = game
        self._rot = 0
        self.drops = drops
        self.age = 0
        self.tag: Optional[str] = None
        self.enemy_names = enemy_names

    def _get_rot(self):
        return self._rot

    def _set_rot(self, rot):
        # print(self.rot)
        self._rot = rot
        self.stop()
        # right
        if self.rot == 1:
            self.forward(self.speed)
            # print("forward")

        # up
        elif self.rot == 0:
            self.strafe(self.speed)
            # print("strafe right")

        # left
        elif self.rot == 3:
            self.reverse(self.speed)
            # print("backward")

        # down
        elif self.rot == 2:
            self.strafe(-self.speed)
            # print("strafe left")

    rot = property(_get_rot, _set_rot)

    def update(self):
        self.age += 1

        col_p = self.collides_with_list(self.game.assets_paths)
        # print(len(col_p))
        # print(self.tag)
        if len(col_p) == 1:
            path = col_p[0]
            if path.target[0] == 0:
                if abs(path.target[1] - self.center_x) <= self.speed:
                    self.center_x = path.target[1]
                    self.rot = path.rot
            elif path.target[0] == 1:
                if abs(path.target[1] - self.center_y) <= self.speed:
                    self.center_y = path.target[1]
                    self.rot = path.rot
            if path.tag == 'f':
                self.tag = 'f'
        elif len(col_p) == 0 and self.tag == 'f':
            self.kill(True)

        super().update()

    def take_damage(self, dmg: int):
        self.hp -= dmg
        if self.hp <= 0:
            self.kill()

    def kill(self, in_finish=False):
        if in_finish:
            self.game.lives -= self.dmg
        else:
            drop_amount = sum(self.drops.values())
            do_spread = drop_amount > 1
            self.game.data += self.dmg
            for e in self.drops.keys():
                cnt = self.drops[e]
                enemy = self.enemy_names[e]
                for i in range(cnt):
                    enemy = enemy.clone()
                    # enemy.position = self.position
                    enemy.rot = self.rot
                    enemy.paths = self.game.assets_paths
                    if do_spread:
                        spread = self._get_spread()
                        enemy.position = self.center_x + self.change_x * spread, \
                                         self.center_y + self.change_y * spread
                    else:
                        enemy.position = self.position
                    self.game.assets_enemies.append(enemy)

        super().kill()

    def _get_spread(self):
        spread = random.random() * ENEMY_SPREAD
        path = self.collides_with_list(self.game.assets_paths)[0]
        if path.rot == self.rot:
            return spread
        else:
            return spread * 0.5

    def clone(self):
        e = Enemy(self.hp, self.speed, self.dmg, self.sprite, self.drops, self.enemy_names, self.game)
        e.tag = self.tag
        return e
