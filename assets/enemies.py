import arcade
import random
from typing import Dict, Optional

import main
import assets

SCALE = 4
ENEMY_SPREAD = 0


class Enemy(arcade.Sprite):

    def __init__(self, hp: int, speed: int, dmg: int, sprite: str, drops: dict,
                 enemy_names: Dict[str, "Enemy"], game: main.TowerDefenseMap, segment):
        super().__init__(sprite, scale=SCALE)
        self.sprite = sprite
        self.hp = hp
        self.speed = speed
        self.dmg = dmg
        self.game = game
        self._rot = 0
        self.drops = drops
        self.age = 0
        self.segment_age = 0
        self._segment: Optional["assets.maps.Segment"] = None
        self.segment: Optional["assets.maps.Segment"] = segment
        self.tag: Optional[str] = None
        self.enemy_names = enemy_names

    def _get_segment(self):
        return self._segment

    def _set_segment(self, segment: "assets.maps.Segment"):
        self._segment = segment
        if segment is not None:
            self.rot = segment.direction

    segment = property(_get_segment, _set_segment)

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
        self.segment_age += self.speed
        if self.segment_age > self.segment.length * SCALE * 16:
            self.segment_age = 0
            try:
                self.segment = self.game.map.segments[self.game.map.segments.index(self.segment)+1]
                self.rot = self.segment.direction
            except IndexError:
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
            self.game.data += self.dmg
            for e in self.drops.keys():
                cnt = self.drops[e]
                enemy = self.enemy_names[e]
                for i in range(cnt):
                    enemy = enemy.clone()
                    # enemy.position = self.position
                    enemy.rot = self.rot
                    enemy.paths = self.game.assets_paths
                    enemy.position = self.position
                    enemy.segment = self.segment
                    enemy.segment_age = self.segment_age  # + random.randrange(ENEMY_SPREAD)

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
        e = Enemy(self.hp, self.speed, self.dmg, self.sprite, self.drops, self.enemy_names, self.game, self.segment)
        e.tag = self.tag
        return e
