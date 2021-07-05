import arcade

SCALE = 4


class Tower(arcade.Sprite):

    def __init__(self, sprite):
        super().__init__(sprite, scale=SCALE)

    def update(self):
        pass


class Path(arcade.Sprite):

    def __init__(self, rot, sprite, pos):
        super().__init__(sprite, scale=SCALE)
        self.rot = rot
        self.turn_right(rot * 90)
        self.center_x = pos[0]*SCALE*16+32
        self.center_y = pos[1]*SCALE*16+32

        # print(pos)
        # print(self.center_x, self.center_y)
        # print()

    def update(self):
        pass


class Enemy(arcade.Sprite):

    def __init__(self, hp, speed, dmg, sprite, drops, path_list):
        super().__init__(sprite, scale=SCALE)
        self.sprite = sprite
        self.hp = hp
        self.speed = speed
        self.dmg = dmg
        self.paths = path_list
        self.rot = 0
        self.drops = drops
        self.age = 0

    def update(self):
        self.age += 1

        self.move()

        col_p = self.collides_with_list(self.paths)
        if len(col_p) == 1:
            self.rot = col_p[0].rot

    def move(self):
        if self.rot == 0:
            self.forward(self.speed)
        elif self.rot == 1:
            self.strafe(self.speed)
        elif self.rot == 2:
            self.reverse(self.speed)
        elif self.rot == 3:
            self.strafe(-self.speed)

        self.center_x += self.change_x
        self.center_y += self.change_y
        self.change_x = 0
        self.change_y = 0

    def kill(self):

        super().kill()

    def clone(self):
        return Enemy(self.hp, self.speed, self.dmg, self.sprite, self.drops, self.paths)


class Bullet(arcade.Sprite):

    def __init__(self, speed, dmg, rot, sprite, enemy_list, pierce=1):
        super().__init__(sprite, scale=SCALE)
        self.turn_right(rot)
        self.speed = speed
        self.dmg = dmg
        self.enemies = enemy_list
        self.pierce = pierce

    def update(self):
        self.forward(self.speed)
        col_e = self.collides_with_list(self.enemies)
        for i in range(self.pierce):
            try:
                col_e[i].kill()
                self.pierce -= 1
            except IndexError:
                pass
            if self.pierce == 0:
                self.kill()
                return


class Map:

    def __init__(self, map, **kwargs):
        self.__dict__.update(kwargs)
        self.map = None
        self.load_map(map)
        #print(self.start)
        #print(self.finish)

    def load_map(self, map_filename):
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
                    map.append(Path(rot, "./resources/images/path.png", (j, i)))
                j += 1
            i += 1
        self.map = map

    def spawn(self, enemy) -> Enemy:
        e = enemy.clone()
        e.center_x = self.start[0]*SCALE*16
        e.center_y = self.start[1]*SCALE*16-32
        return e
