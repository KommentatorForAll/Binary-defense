from typing import Optional, Dict, Tuple, List

import arcade
import numpy as np
import random

import main

SCALE = 4
ENEMY_SPREAD = 25


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
            self.game.data += 1
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
        return Enemy(self.hp, self.speed, self.dmg, self.sprite, self.drops, self.enemy_names, self.game)


class Map:

    def __init__(self, map_name: str, **kwargs):
        self.start: tuple = (0, 0)
        self.finish: tuple = (0, 0)
        print("creating map")
        self.__dict__.update(kwargs)
        self.map: arcade.SpriteList = self.load_map(map_name)

    def load_map(self, map_filename: str):
        # print("loading map")
        map_sprites = arcade.SpriteList(use_spatial_hash=True)
        map_file = open("./resources/maps/" + map_filename)
        map_data = map_file.read().split("\n")
        i = 0
        map_data.reverse()
        # print(self.finish)
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
                    # print(j, i)
                    if (j, i) == self.start:
                        # self.start_path = path
                        path.tag = 's'
                    elif [j, i] == self.finish:
                        # print("found finish")
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
            # print(self.hitbox_color)
            self.draw_hit_box(self.hitbox_color, 2)
        self.bullets.draw(**kwargs)

    def clone(self) -> "Tower":
        raise NotImplementedError


class Bullet(arcade.AnimatedTimeBasedSprite):

    def __init__(self, speed: int, dmg: int, rot: float, sprite: str, origin: Tower, enemy_list: arcade.SpriteList,
                 pierce: int = 1):
        super().__init__(sprite, scale=SCALE)
        self.turn_right(rot)
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
        angle = get_angle_pnt(self.position, enemy.position)
        b = Bullet(5, self.dmg, angle, "./resources/images/fireball.png", self, self.enemies, pierce=1)
        b.position = self.position
        self.bullets.append(b)
        super().shoot(enemy)

    def clone(self) -> Tower:
        return Proxy(self.enemies)


class Clam(Tower):

    def __init__(self, enemy_list: arcade.SpriteList):
        super().__init__(2, 150, 400, "./resources/images/clam_tk.png", enemy_list)

    def shoot(self, enemy: Enemy):
        angle = get_angle_pnt(self.position, enemy.position)
        b = Bullet(20, self.dmg, angle, "./resources/images/laser_0.png", self, self.enemies, pierce=4)
        b.position = self.position
        self.bullets.append(b)
        super().shoot(enemy)

    def clone(self) -> Tower:
        return Clam(self.enemies)


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


class ShopItem(arcade.Sprite):

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)
        super().__init__(kwargs["img"], scale=kwargs["scale"] if kwargs.keys().__contains__("scale") else 1)
        self.tower: Tower = self.tower
        self.price: int = self.price
        self.name: str = self.name
        self.description: str = self.description


class Shop:

    def __init__(self, towers: List[Dict[str, any]], pos: tuple,
                 game: main.TowerDefenceMap,
                 scale: float = 2
                 ):
        self.towers: List[ShopItem] = [ShopItem(scale=SCALE/2, **kwargs) for kwargs in towers]
        self.shop_sprites: Dict[arcade.Sprite, Tower] = {}
        self.sprites: arcade.SpriteList = arcade.SpriteList()
        self.scale: float = scale
        self.pos: tuple = pos
        self.width: int = 0
        self.offset: tuple = (50, 50)
        self.cur_price: int = 0
        self.hitbox_color_not_placeable = arcade.csscolor.RED
        self.hitbox_color_placeable = arcade.csscolor.GREEN

        self.game = game
        # self.path_list = path_list
        # self.tower_list = tower_list

        self.hold_object: Optional[Tower] = None

        self.col_checker: arcade.Sprite = arcade.SpriteCircle(4, (255, 0, 0))

        self.setup()

    def setup(self):
        spacing = 75
        total_width = len(self.towers) * spacing + self.offset[1] * 2
        print(f"total width: {total_width}, pos: {self.pos}, offset: {self.offset}")
        i = self.pos[0] - total_width / 2 + self.offset[1]
        for spr in self.towers:
            spr.position = (i, self.pos[1])

            self.sprites.append(spr)

            i += spacing
        i -= spacing
        i += self.offset[0] * 2
        self.width = total_width

    def draw(self, **kwargs):
        arcade.draw_rectangle_filled(self.pos[0], self.pos[1], self.width,
                                     self.offset[1] * 2, (0, 127, 0))
        self.sprites.draw(**kwargs)

    def on_mouse_press(self, x, y, button, modifiers):
        self.col_checker.position = x, y
        clicked_sprites = self.col_checker.collides_with_list(self.sprites)
        if len(clicked_sprites) != 0:
            print(f"clicked on {clicked_sprites[0]}")
            obj: ShopItem = clicked_sprites[0]
            if obj.price > self.game.data:
                self.game.info_ui.warn_text = "Not enough data to buy"
                return
            self.hold_object = obj.tower.clone()
            self.cur_price = obj.price
            self.hold_object.activated = False
            self.hold_object.selected = True
            self.game.assets_towers.append(self.hold_object)
        else:
            print("didn't click on shop item")

    def on_mouse_release(self, x, y, button, modifiers):
        if self.hold_object is None:
            return
        else:
            self.hold_object.position = x, y
            cols: list = self.hold_object.collides_with_list(self.game.assets_towers)
            cols.extend(self.hold_object.collides_with_list(self.game.assets_paths))
            if len(cols) > 0:
                self.game.assets_towers.remove(self.hold_object)
                self.hold_object = None
                return
            self.hold_object.selected = False
            self.hold_object.activated = True

            self.game.data -= self.cur_price

            self.hold_object = None

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        if self.hold_object is None:
            return
        else:
            self.hold_object.position = x, y
            cols: list = self.hold_object.collides_with_list(self.game.assets_paths)
            cols.extend(self.hold_object.collides_with_list(self.game.assets_towers))
            if len(cols) > 0:
                # print("not placeable")
                self.hold_object.hitbox_color = self.hitbox_color_not_placeable
            else:
                # print("placeable")
                self.hold_object.hitbox_color = self.hitbox_color_placeable


class InfoUI:

    def __init__(self, game: main.TowerDefenceMap):
        self.game = game
        self.size = (250, main.WINDOW_HEIGHT)
        self.topleft_pos = (main.WINDOW_WIDTH - self.size[0], main.WINDOW_HEIGHT)
        self.center_pos = (main.WINDOW_WIDTH - (self.size[0] / 2), main.WINDOW_HEIGHT / 2)
        self.sprites = arcade.SpriteList()
        self.data_text: arcade.Sprite = arcade.Sprite("./resources/images/text_data.png", scale=SCALE)
        self.lives_text: arcade.Sprite = arcade.Sprite("./resources/images/text_lives.png", scale=SCALE)
        self._warn_text: str = ""
        self._warn_age = 0
        self._age_warn = False
        self.default_offset: Tuple[int, int] = (20, 0)
        self.setup()

    def _get_warn_text(self):
        return self._warn_text

    def _set_warn_text(self, text: str):
        self._warn_text = text
        self._warn_age = 0
        self._age_warn = True

    warn_text = property(_get_warn_text, _set_warn_text)

    def setup(self):
        self.data_text.position = self.topleft_pos[0] + self.default_offset[0], self.topleft_pos[1] - 48

        self.lives_text.position = self.topleft_pos[0] + self.default_offset[0], self.topleft_pos[1] - 128

        # self.sprites.append(self.data_text)
        # self.sprites.append(self.lives_text)

    def update(self):
        if self._age_warn:
            self._warn_age += 1
            if self._warn_age > 100:
                self._warn_text = ""
                self._age_warn = False

    def draw(self, **kwargs):
        arcade.draw_rectangle_filled(self.center_pos[0], self.center_pos[1], self.size[0], self.size[1], (0, 0, 128))
        self.sprites.draw(**kwargs)

        arcade.draw_text(f"Data: {self.game.data}",
                         self.data_text.position[0],
                         self.data_text.position[1],
                         (0, 255, 0),
                         font_name="./resources/fonts/Welbut",
                         font_size=7 * SCALE,
                         anchor_x="left",
                         )

        arcade.draw_text(f"Lives: {self.game.lives}",
                         self.lives_text.position[0],
                         self.lives_text.position[1],
                         (0, 255, 0),
                         font_name="./resources/fonts/Welbut",
                         font_size=7 * SCALE,
                         anchor_x="left"
                         )

        arcade.draw_text(self.warn_text,
                         self.topleft_pos[0] + self.default_offset[0],
                         self.topleft_pos[1] - main.WINDOW_HEIGHT + 50,
                         (255, 0, 0),
                         font_name="./resources/fonts/Welbut",
                         font_size=3 * SCALE,
                         anchor_x="left"
                         )


def get_angle_pnt(p1, p2) -> float:
    return get_angle((0, 1), (p2[1] - p1[1], p2[0] - p1[0]))


def get_angle(v0, v1) -> float:
    angle = np.math.atan2(np.linalg.det([v0, v1]), np.dot(v0, v1))
    return +np.degrees(angle)
