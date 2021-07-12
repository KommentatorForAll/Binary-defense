import arcade
import numpy as np
from typing import Optional, Union
import random

from assets.enemies import Enemy

SCALE = 4


class Tower(arcade.Sprite):

    def __init__(self,
                 dmg: float,
                 cooldown: int,
                 radius: int,
                 sprite: str,
                 enemy_list: arcade.SpriteList,
                 sound: Union[str, arcade.Sound] = None
                 ):
        super().__init__(sprite, scale=SCALE, hit_box_algorithm='Simple')
        self.dmg: float = dmg
        self.tick = 0
        self.max_cooldown: int = cooldown
        self.cooldown: int = cooldown
        self.radius: int = radius
        self.enemies: arcade.SpriteList = enemy_list
        self.bullets: arcade.SpriteList = arcade.SpriteList()
        self.range_detector: arcade.Sprite = arcade.SpriteCircle(self.radius, (255, 0, 0))
        self.range_detector.position = self.position
        self.activated: bool = True
        self.selected: bool = False
        self.placeable: bool = True
        self.sound: Optional[arcade.Sound] = None
        if sound is not None:
            if isinstance(sound, arcade.Sound):
                self.sound = sound
            else:
                self.sound = arcade.load_sound(sound)

    def update(self):
        self.tick = not self.tick
        self.range_detector.position = self.position

        if not self.activated:
            return

        self.bullets.update()
        self.cooldown -= 1
        # self.collision_radius = range
        if self.cooldown <= 0:
            col_e = self.range_detector.collides_with_list(self.enemies)
            if len(col_e) > 0:
                # add enemy selection system
                self.shoot(col_e[0])

    def shoot(self, enemy: Enemy):
        self.cooldown = self.max_cooldown
        if self.sound is not None:
            arcade.play_sound(self.sound)

    def kill(self):
        super().kill()

    def draw(self, **kwargs):
        if self.selected:
            self.range_detector.draw_hit_box((255, 0, 0), 2)
        if not self.activated:
            self._hit_box_shape = None
            self.draw_hit_box(arcade.csscolor.GREEN if self.placeable else arcade.csscolor.RED, 3)
        self.bullets.draw(**kwargs)

    def clone(self) -> "Tower":
        raise NotImplementedError


class Bullet(arcade.AnimatedTimeBasedSprite):

    def __init__(self, speed: int, dmg: float, rot: float, sprite: str, origin: Tower, enemy_list: arcade.SpriteList,
                 pierce: int = 1, scale=SCALE):
        super().__init__(sprite, scale=scale)
        self.turn_right(rot)
        self.forward(speed)
        self.dmg: float = dmg
        self.enemies: arcade.SpriteList = enemy_list
        self.pierce: int = pierce
        self.origin: Tower = origin
        self.collided_with: list = []

    def update(self):
        super().update()

        col_e = self.collides_with_list(self.enemies)
        for i in range(self.pierce):
            try:
                if col_e[i] in self.collided_with:
                    continue
                col_e[i].take_damage(self.dmg)
                self.collided_with.append(col_e[i])
                self.pierce -= 1
            except IndexError:
                break
            if self.pierce == 0:
                self.kill()
                return

        if arcade.get_distance_between_sprites(self, self.origin) > self.origin.radius:
            self.kill()
            return


class Firewall(Tower):

    def __init__(self, enemy_list: arcade.SpriteList):
        super().__init__(1, 100, 256, "./resources/images/firewall.png", enemy_list, "./resources/sounds/fire_ball.mp3")

    def shoot(self, enemy: Enemy):
        super().shoot(enemy)
        for i in range(0, 359, 45):
            b = Bullet(5, self.dmg, i, "./resources/images/fireball.png", self, self.enemies)
            self.bullets.append(b)
            b.position = self.position

    def clone(self) -> Tower:
        return Firewall(self.enemies)


class Proxy(Tower):

    def __init__(self, enemy_list: arcade.SpriteList):
        super().__init__(2, 100, 256, "./resources/images/proxy.png", enemy_list, "./resources/sounds/fire_ball.mp3")

    def shoot(self, enemy: Enemy):
        angle = get_angle_pnt(self.position, enemy.position)
        b = Bullet(5, self.dmg, angle, "./resources/images/fireball.png", self, self.enemies, pierce=1)
        b.position = self.position
        self.bullets.append(b)
        super().shoot(enemy)

    def clone(self) -> Tower:
        return Proxy(self.enemies)


class Clam(Tower):

    def __init__(self, enemy_list: arcade.SpriteList):
        super().__init__(2, 150, 400, "./resources/images/clam_tk.png", enemy_list, "./resources/sounds/laser.mp3")

    def shoot(self, enemy: Enemy):
        angle = get_angle_pnt(self.position, enemy.position)
        b = Bullet(20, self.dmg, angle, "./resources/images/laser_0.png", self, self.enemies, pierce=4)
        b.position = self.position
        self.bullets.append(b)
        super().shoot(enemy)

    def clone(self) -> Tower:
        return Clam(self.enemies)


class Spinner(Tower):

    def __init__(self, enemy_list: arcade.SpriteList):
        super().__init__(0.25, 8, 256, "./resources/images/spinner.png", enemy_list, "./resources/sounds/nya.mp3")
        self.__rot = 0
        self.does_trigger = 0

    def shoot(self, enemy: Enemy):
        self.__rot += 16
        b = Bullet(10, self.dmg, self.__rot, "./resources/images/trans_heart.png", self, self.enemies)
        b.position = self.position
        self.bullets.append(b)
        b = Bullet(10, self.dmg, self.__rot+180, "./resources/images/trans_heart.png", self, self.enemies)
        b.position = self.position
        self.bullets.append(b)
        if self.does_trigger > 3:
            super().shoot(enemy)
            self.does_trigger = 0
        else:
            self.cooldown = self.max_cooldown
            self.does_trigger += 1

    def clone(self):
        return Spinner(self.enemies)


class Defender(Tower):

    def __init__(self, enemy_list: arcade.SpriteList):
        super().__init__(1, 30, 256,
                         "./resources/images/windows_defender.png", enemy_list, "./resources/sounds/windoof_error.mp3")

    def shoot(self, enemy: Enemy):
        angle = get_angle_pnt(self.position, enemy.position)
        b = Bullet(12,
                   self.dmg,
                   angle + random.randrange(-5, 5),
                   "./resources/images/energy_pebble.png",
                   self,
                   self.enemies,
                   scale=2
                   )
        b.position = self.position
        self.bullets.append(b)
        super().shoot(enemy)

    def clone(self):
        return Defender(self.enemies)


def get_angle_pnt(p1, p2) -> float:
    return get_angle((0, 1), (p2[1] - p1[1], p2[0] - p1[0]))


def get_angle(v0, v1) -> float:
    angle = np.math.atan2(np.linalg.det([v0, v1]), np.dot(v0, v1))
    return +np.degrees(angle)
