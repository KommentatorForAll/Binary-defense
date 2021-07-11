import random
from typing import List, Dict

import arcade

import main
from assets.enemies import Enemy

SCALE = 4


class Path(arcade.Sprite):

    def __init__(self, rot: int, pos: tuple, tag: str = None):
        super().__init__("./resources/images/path_bg.png", scale=SCALE)
        self.fg = arcade.Sprite("./resources/images/path_fg.png", scale=SCALE)
        self.rot = rot
        self.turn_right(rot * 90)
        self.pos = pos
        self.center_x = pos[0] * SCALE * 16 + 32
        self.center_y = pos[1] * SCALE * 16 + 32
        x_incr = int(rot == 1) - int(rot == 3)
        y_incr = int(rot == 0) - int(rot == 2)
        self.fg.position = self.center_x + x_incr * SCALE * 2, self.center_y + y_incr * SCALE * 2
        self.fg.turn_right(rot*90)
        self.fgsl = arcade.SpriteList(use_spatial_hash=True)
        self.fgsl.append(self.fg)
        self.target: tuple = self.set_target()
        self.tag: str = tag
        self.set_target()

    def _get_tag(self):
        return self._tag

    def _set_tag(self, tag: str):
        self._tag = tag
        if tag == 'f' or tag == 's':
            self.fg.texture = arcade.load_texture("./resources/images/path_fg_arrow.png")

    tag = property(_get_tag, _set_tag)

    def set_target(self):
        if self.rot % 2 == 0:
            target = (0, self.center_x)
        else:
            target = (1, self.center_y)
        return target

    def update(self):
        pass

    def draw(self, **kwargs):
        self.fgsl.draw(**kwargs)


class Segment:

    def __init__(self, direction: int, length: int):
        self.direction = direction
        self.length = length
        self.x_incr = int(direction == 1) - int(direction == 3)
        self.y_incr = int(direction == 0) - int(direction == 2)

    def __str__(self):
        return f"{self.direction},{self.length}"

    def print(self):
        print(f"Segment: direction {self.direction}; length {self.length}; x {self.x_incr}; y {self.y_incr}")


class Map:

    def __init__(self, map_name: str, local_map=True):
        self.start: tuple = (0, 0)
        self.finish: tuple = (0, 0)
        print("creating map")
        self.data: int = 0
        self.lives: int = 0
        self.segments: List[Segment] = []
        self.map: arcade.SpriteList = self.load_map(map_name, local_map)

    def load_map(self, map_filename: str, local_map=True):
        map_sprites = arcade.SpriteList(use_spatial_hash=True)
        map_file = open(f"./resources/maps/{map_filename}" if local_map else map_filename)
        map_data = map_file.read().split(";")
        self.lives = int(map_data[0])
        self.data = int(map_data[1])
        self.start = [int(x) for x in map_data[2].split(",")]
        print(map_data)
        map_data = map_data[3:]
        print(map_data)
        x, y = self.start
        cnt = 0
        path = None
        for s in map_data:
            info = [int(x) for x in s.split(",")]
            segment = Segment(*info)
            print(segment)
            self.segments.append(segment)
            for i in range(segment.length):
                if cnt == 1:
                    path = Path(info[0], (x, y), 's')
                else:
                    path = Path(info[0], (x, y))
                cnt += 1
                map_sprites.append(path)
                x += segment.x_incr
                y += segment.y_incr
        path.tag = 'f'
        map_sprites.reverse()
        return map_sprites

    def spawn(self, enemy: Enemy) -> Enemy:
        e = enemy.clone()
        e.position = self.start[0] * SCALE * 16 + (32 if self.start[0] >= 0 else 0), \
            self.start[1] * SCALE * 16 + (0 if self.start[1] <= 0 else 32)
        e.segment = self.segments[0]
        e.segment_age = -27
        return e


class Wave:

    def __init__(self, enemies: List[Dict[str, any]], game_map: Map, game: main.TowerDefenceMap):
        self.cnt: int = 0
        self.delay: int = 0
        self.game_map: Map = game_map
        self.game: main.TowerDefenceMap = game
        self.enemies = enemies
        self.e_ind = random.randrange(len(enemies))

    def update(self):
        self.delay -= 1
        if self.delay <= 0:
            if len(self.enemies) == 0:
                return
            self.game.assets_enemies.append(self.game_map.spawn(self.enemies[self.e_ind]["enemy"]))
            self.delay = self.enemies[self.e_ind]["delay"]

            self.enemies[self.e_ind]["cnt"] -= 1
            if self.enemies[self.e_ind]["cnt"] == 0:
                self.enemies.remove(self.enemies[self.e_ind])
            left_over_es = len(self.enemies)
            if left_over_es > 0:
                self.e_ind = random.randrange(left_over_es)
            else:
                self.finish_wave()

    def finish_wave(self):
        self.game.finish_wave()
