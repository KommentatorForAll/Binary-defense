import arcade

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
