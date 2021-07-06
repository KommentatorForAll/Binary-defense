from typing import Optional, Dict

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
        self.target: tuple = self.set_target()
        self.tag: str = tag
        self.set_target()

    def set_target(self):
        if self.rot % 2 == 0:
            target = (0, self.center_x)
        else:
            target = (1, self.center_y)
        return target

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
        self.tag: Optional[str] = None

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

    def __init__(self, map_name: str, **kwargs):
        self.start: tuple = (0, 0)
        self.finish: tuple = (0, 0)
        self.map: arcade.SpriteList = self.load_map(map_name)
        self.__dict__.update(kwargs)
        self.load_map(map_name)
        # print(self.start)
        # print(self.finish)

    def load_map(self, map_filename: str):
        map_sprites = arcade.SpriteList(use_spatial_hash=True)
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
                    path = Path(rot, "./resources/images/path.png", (j, i))
                    if (j, i) == self.start:
                        # self.start_path = path
                        path.tag = 's'
                    elif (j, i) == self.finish:
                        path.tag = 'f'
                    map_sprites.append(path)
                j += 1
            i += 1
        return map_sprites

    def spawn(self, enemy: Enemy) -> Enemy:
        e = enemy.clone()
        e.paths = self.map
        e.position = self.start[0] * SCALE * 16, self.start[1] * SCALE * 16 - 32
        return e


class Tower(arcade.Sprite):

    def __init__(self, dmg: int, cooldown: int, radius: int, sprite: str, enemy_list: arcade.SpriteList):
        super().__init__(sprite, scale=SCALE, hit_box_algorithm='Simple')
        self.dmg: int = dmg
        self.max_cooldown: int = cooldown
        self.cooldown: int = cooldown
        self.radius: int = radius
        self.enemies: arcade.SpriteList = enemy_list
        self.bullets: arcade.SpriteList = arcade.SpriteList()
        self.range_detector: arcade.Sprite = arcade.SpriteCircle(self.radius, (255, 0, 0))
        self.range_detector.position = self.position
        self.activated: bool = True
        self.selected: bool = False
        self.hitbox_color: arcade.csscolor = arcade.csscolor.RED

    def update(self):
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

    def kill(self):
        super().kill()

    def draw(self, **kwargs):
        if self.selected:
            self.range_detector.draw_hit_box((255, 0, 0), 2)
        if not self.activated:
            print(self.hitbox_color)
            self.draw_hit_box(self.hitbox_color, 2)
        self.bullets.draw(**kwargs)
        super().draw()

    def clone(self) -> "Tower":
        raise NotImplementedError


class Bullet(arcade.Sprite):

    def __init__(self, speed: int, dmg: int, rot: float, sprite: str, origin: Tower, enemy_list: arcade.SpriteList,
                 pierce: int = 1):
        super().__init__(sprite, scale=SCALE)
        self.turn_right(rot)
        print(rot)
        self.forward(speed)
        self.dmg: int = dmg
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
        super().__init__(1, 100, 256, "./resources/images/firewall.png", enemy_list)

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
        super().__init__(2, 100, 256, "./resources/images/proxy.png", enemy_list)

    def shoot(self, enemy: Enemy):
        print(get_angle((1, 0), (enemy.center_y - self.center_y, enemy.center_x - self.center_x)))
        b = Bullet(5, self.dmg, +get_angle((0, 1), (enemy.center_y - self.center_y, enemy.center_x - self.center_x)),
                   "./resources/images/fireball.png", self, self.enemies, pierce=1)
        # print(b)
        b.position = self.position
        self.bullets.append(b)
        super().shoot(enemy)

    def clone(self) -> Tower:
        return Proxy(self.enemies)


class Surface:

    def __init__(self, name="surface"):
        self.name = name
        self.sprites = arcade.SpriteList()
        self._offset = (0, 0)

    def add_sprite(self, sprite: arcade.Sprite):
        self.sprites.append(sprite)

    def _get_offset(self):
        return self._offset

    def _set_offset(self, offset):
        self._offset = offset

    def draw(self):
        self.sprites.draw()

    offset = property(_get_offset, _set_offset)


class Shop:

    def __init__(self, towers: Dict[str, Tower], pos: tuple, path_list: arcade.SpriteList, tower_list: arcade.SpriteList, scale: float = 2):
        self.towers: Dict[str, Tower] = towers
        self.shop_sprites: Dict[arcade.Sprite, Tower] = {}
        self.sprites: arcade.SpriteList = arcade.SpriteList()
        self.scale: float = scale
        self.pos: tuple = pos
        self.width: int = 0
        self.offset: tuple = (50, 50)
        self.hitbox_color_not_placeable = arcade.csscolor.RED
        self.hitbox_color_placeable = arcade.csscolor.GREEN

        self.path_list = path_list
        self.tower_list = tower_list

        self.hold_object: Optional[Tower] = None

        self.col_checker: arcade.Sprite = arcade.SpriteCircle(4, (255, 0, 0))

        self.setup()

    def setup(self):
        spacing = 75
        total_width = len(self.towers)*spacing + self.offset[1]*2
        print(f"total width: {total_width}, pos: {self.pos}, offset: {self.offset}")
        i = self.pos[0]-total_width/2 + self.offset[1]
        for img_name, tower in self.towers.items():
            spr = arcade.Sprite(img_name, scale=self.scale)
            spr.position = (i, self.pos[1])

            self.shop_sprites[spr] = self.towers[img_name]

            self.sprites.append(spr)

            i += spacing
        i -= spacing
        i += self.offset[0]*2
        self.width = total_width

    def draw(self, **kwargs):
        arcade.draw_rectangle_filled(self.pos[0], self.pos[1], self.width,
                                     self.offset[1]*2, (0, 127, 0))
        self.sprites.draw(**kwargs)

    def on_mouse_press(self, x, y, button, modifiers):
        self.col_checker.position = x, y
        clicked_sprites = self.col_checker.collides_with_list(self.sprites)
        if len(clicked_sprites) != 0:
            print(f"clicked on {clicked_sprites[0]}")
            self.hold_object = self.shop_sprites[clicked_sprites[0]].clone()
            self.hold_object.activated = False
            self.hold_object.selected = True
            self.tower_list.append(self.hold_object)
        else:
            print("didn't click on shop item")

    def on_mouse_release(self, x, y, button, modifiers):
        if self.hold_object is None:
            return
        else:
            self.hold_object.position = x, y
            cols: list = self.hold_object.collides_with_list(self.path_list)
            cols.extend(self.hold_object.collides_with_list(self.tower_list))
            print(len(cols))
            if len(self.hold_object.collides_with_list(self.path_list)) > 0 \
                    or len(self.hold_object.collides_with_list(self.tower_list)) > 0:
                self.tower_list.remove(self.hold_object)
                self.hold_object = None
                return
            self.hold_object.selected = False
            self.hold_object.activated = True

            self.hold_object = None

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        if self.hold_object is None:
            return
        else:
            self.hold_object.position = x, y
            cols: list = self.hold_object.collides_with_list(self.path_list)
            cols.extend(self.hold_object.collides_with_list(self.tower_list))
            if len(self.hold_object.collides_with_list(self.path_list)) > 0 \
                    or len(self.hold_object.collides_with_list(self.tower_list)) > 0:
                print("not placeable")
                self.hold_object.hitbox_color = self.hitbox_color_not_placeable
            else:
                print("placeable")
                self.hold_object.hitbox_color = self.hitbox_color_placeable


def get_angle(v0, v1) -> float:
    angle = np.math.atan2(np.linalg.det([v0, v1]), np.dot(v0, v1))
    return +np.degrees(angle)
