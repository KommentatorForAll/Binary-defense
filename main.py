import os
import time

import arcade
import assets
from pyglet.gl import GL_NEAREST


class TowerDefence(arcade.Window):

    def __init__(self):
        super().__init__(1280, 720, "Binary Defence")

        arcade.set_background_color((0, 0, 0))

        self.set_update_rate(1/20)

        # self.assets_all = None
        self.assets_paths = None
        self.assets_enemies = None
        self.assets_towers = None

        self.availables_enemies = None
        self.availables_maps = None
        self.t0 = time.time()

        self.map = None

        self.setup()

    def setup(self):
        # self.assets_all = arcade.SpriteList()
        self.assets_paths = arcade.SpriteList(use_spatial_hash=True)
        self.assets_enemies = arcade.SpriteList()
        self.assets_towers = arcade.SpriteList(use_spatial_hash=True)

        self.availables_enemies = {}
        self.availables_maps = {}

        self.load_availables()
        print(self.availables_enemies)

    def load_availables(self):

        # Enemies
        enemy_file = open("resources/infos/enemies.txt")
        enemies = enemy_file.read().split("\n")
        for enemy in enemies:
            if enemy[0] == "#":
                continue
            e_info = enemy.split(" ")
            drops = {}
            l = len(e_info)
            if l > 5:
                i = 5
                while i < l:
                    drops[e_info[i]] = int(e_info[i + 1])
                    i += 2
            self.availables_enemies[e_info[0]] = assets.Enemy(int(e_info[2]), int(e_info[3]), int(e_info[4]),
                                                              f"resources/images/{e_info[1]}", drops, self.assets_paths)

        enemy_file.close()

        # Towers
        tower_file = open("resources/infos/towers.txt")
        towers = tower_file.read().split("\n")
        for tower in towers:
            if tower[0] == "#":
                continue
            t_info = tower.split(" ")

        # Maps
        for filename in os.listdir("resources/maps"):
            if not filename.endswith(".mapinfo"):
                continue
            map_name = filename[:-8]
            print(map_name)
            kwargs = {}
            for info in open(f"./resources/maps/{filename}").read().split("\n"):
                k, v = info.split("=")
                kwargs[k] = [int(x) for x in v.split(",")] if v.find(",") != -1 else v
                # print(kwargs[k])
            self.availables_maps[map_name] = assets.Map(**kwargs)
            # self.availables_maps[map_name] = map

    def load_map(self, map_name):
        self.map = self.availables_maps[map_name]
        self.assets_paths = self.map.map
        self.assets_enemies.append(self.map.spawn(self.availables_enemies["enemy_1"]))

    def on_update(self, delta_time):
        self.assets_paths.update()
        self.assets_enemies.update()
        self.assets_towers.update()

    def on_draw(self):
        arcade.start_render()

        self.assets_paths.draw(filter=GL_NEAREST)
        self.assets_towers.draw(filter=GL_NEAREST)
        self.assets_enemies.draw(filter=GL_NEAREST)

    def update(self, delta_time):
        pass


def main():
    td = TowerDefence()
    td.load_map("0")
    arcade.run()


if __name__ == "__main__":
    main()
