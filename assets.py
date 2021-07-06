import arcade
import numpy as np

SCALE = 4


class Path(arcade.Sprite):

    def __init__(self, rot: int, sprite: str, pos: tuple, tag: str = None):
        super().__init__(sprite, scale=SCALE)
        self.rot = rot
        self.turn_right(rot * 90)
        self.pos = pos
        self.center_x = pos[0] * SCALE * 16 + 32
        self.center_y = pos[1] * SCALE * 16 + 32
        self.target = None
        self.tag = tag
        self.set_target()

    def set_target(self):
        if self.rot % 2 == 0:
            self.target = (0, self.center_x)
        else:
            self.target = (1, self.center_y)

    def update(self):
        pass


class Enemy(arcade.Sprite):

    def __init__(self, hp: int, speed: int, dmg: int, sprite: str, drops: dict, path_list: arcade.SpriteList):
        super().__init__(sprite, scale=SCALE)
        self.sprite = sprite
        self.hp = hp
        self.speed = speed
        self.dmg = dmg
        self.paths = path_list
        self._rot = 0
        self.drops = drops
        self.age = 0
        self.tag = None

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

        col_p = self.collides_with_list(self.paths)
        if len(col_p) == 1:
            path = col_p[0]
            if path.target[0] == 0:
                if abs(path.target[1]-self.center_x) <= self.speed:
                    self.center_x = path.target[1]
                    self.rot = path.rot
            elif path.target[0] == 1:
                if abs(path.target[1]-self.center_y) <= self.speed:
                    self.center_y = path.target[1]
                    self.rot = path.rot
            if path.tag == 'f':
                self.tag = 'f'
        elif len(col_p) == 0 and self.tag == 'f':
            self.kill()

        super().update()

    def take_damage(self, dmg: int):
        self.hp -= dmg
        if self.hp <= 0:
            self.kill()

    def kill(self):

        super().kill()

    def clone(self):
        return Enemy(self.hp, self.speed, self.dmg, self.sprite, self.drops, self.paths)


class Map:

    def __init__(self, map: str, **kwargs):
        self.start = (0, 0)
        self.finish = (0, 0)
        self.map = None
        self.start_path = None
        self.__dict__.update(kwargs)
        self.load_map(map)
        # print(self.start)
        # print(self.finish)

    def load_map(self, map_filename: str):
        map = arcade.SpriteList(use_spatial_hash=True)
        map_file = open("./resources/maps/" + map_filename)
        map_data = map_file.read().split("\n")
        i = 0
        map_data.reverse()
        for row in map_data:
            j = 0
            for p in row:
                if p == '#':
                    pass
                elif p == '-':
                    pass
                else:
                    rot = int(p)
                    tag = None
                    path = Path(rot, "./resources/images/path.png", (j, i))
                    if (j, i) == self.start:
                        self.start_path = path
                        path.tag = 's'
                    elif (j, i) == self.finish:
                        path.tag = 'f'
                    map.append(path)
                j += 1
            i += 1
        self.map = map

    def spawn(self, enemy: Enemy) -> Enemy:
        e = enemy.clone()
        e.paths = self.map
        e.position = self.start[0] * SCALE * 16, self.start[1] * SCALE * 16 - 32
        return e


class Tower(arcade.Sprite):

    def __init__(self, dmg: int, cooldown: int, range: int, sprite: str, enemy_list: arcade.SpriteList):
        super().__init__(sprite, scale=SCALE, hit_box_algorithm='Simple')
        self.dmg = dmg
        self.max_cooldown = cooldown
        self.cooldown = cooldown
        self.range = range
        self.enemies = enemy_list
        self.bullets = arcade.SpriteList()
        self.range_detector = arcade.SpriteCircle(self.range, (255, 0, 0))
        self.range_detector.position = self.position

    def update(self):
        self.range_detector.position = self.position

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

    def kill(self):
        super().kill()

    def draw(self, **kwargs):
        self.range_detector.draw_hit_box((255, 0, 0), 2)
        self.bullets.draw(**kwargs)
        super().draw()


class Bullet(arcade.Sprite):

    def __init__(self, speed: int, dmg: int, rot: float, sprite: str, origin: Tower, enemy_list: arcade.SpriteList, pierce: int = 1):
        super().__init__(sprite, scale=SCALE)
        self.turn_right(rot)
        print(rot)
        self.forward(speed)
        self.speed = speed
        self.dmg = dmg
        self.enemies = enemy_list
        self.pierce = pierce
        self.origin = origin
        self.collided_with = []

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

        if arcade.get_distance_between_sprites(self, self.origin) > self.origin.range:
            self.kill()
            return


class Firewall(Tower):

    def __init__(self, enemy_list: arcade.SpriteList):
        super().__init__(1, 100, 256, "./resources/images/firewall.png", enemy_list)

    def shoot(self, enemy: Enemy):
        super().shoot(enemy)
        for i in range(0, 359, 45):
            b = Bullet(5, self.dmg, i, "./resources/images/fireball.png", self, self.enemies)
            self.bullets.append(b)
            b.position = self.position


class Proxy(Tower):

    def __init__(self, enemy_list: arcade.SpriteList):
        super().__init__(2, 100, 256, "./resources/images/proxy.png", enemy_list)

    def shoot(self, enemy: Enemy):
        print(get_angle((1, 0), (enemy.center_y - self.center_y, enemy.center_x - self.center_x)))
        b = Bullet(5, self.dmg, +get_angle((0, 1), (enemy.center_y - self.center_y, enemy.center_x - self.center_x)),
                   "./resources/images/fireball.png", self, self.enemies, pierce=1)
        # print(b)
        b.position = self.position
        self.bullets.append(b)
        super().shoot(enemy)


def get_angle(v0, v1):
    angle = np.math.atan2(np.linalg.det([v0, v1]), np.dot(v0, v1))
    return np.degrees(angle)
