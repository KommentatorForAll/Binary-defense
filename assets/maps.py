from typing import List, Tuple, Dict

import arcade
import random

import main
from assets.enemies import Enemy

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


class Segment:

    def __init__(self, direction: int, length: int):
        self.direction = direction
        self.length = length
        self.x_incr = direction == 1 - (direction == 3)
        self.y_incr = direction == 0 - (direction == 2)

    def __str__(self):
        return f"Segment: direction {self.direction}; length {self.length}"


class Map:

    def __init__(self, map_name: str, **kwargs):
        self.start: tuple = (0, 0)
        self.finish: tuple = (0, 0)
        print("creating map")
        self.__dict__.update(kwargs)
        self.data: int = self.data
        self.lives: int = self.lives
        self.segments: List[Segment] = []
        self.map: arcade.SpriteList = self.load_map(map_name)

    def load_map(self, map_filename: str):
        map_sprites = arcade.SpriteList(use_spatial_hash=True)
        map_file = open(f"./resources/maps/{map_filename}")
        map_data = map_file.read().split(";")
        self.start = [int(x) for x in map_data[0].split(",")]
        map_data = map_data[1:]
        for s in map_data:
            self.segments.append(Segment(*[int(x) for x in s.split(",")]))

        return map_sprites

    def load_map_old(self, map_filename: str):
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
        e.position = self.start[0] * SCALE * 16, self.start[1] * SCALE * 16 + 32
        e.segment = self.segments[0]
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
