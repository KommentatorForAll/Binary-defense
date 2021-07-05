import os

import arcade
import assets


class TowerDefence(arcade.Window):

    def __init__(self):
        super().__init__(1280, 720, "Binary Defence")

        arcade.set_background_color((0, 0, 0))

        # self.assets_all = None
        self.assets_paths = None
        self.assets_enemies = None
        self.assets_towers = None

        self.availables_enemies = None
        self.availables_maps = None

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
            self.availables_enemies[e_info[0]] = assets.Enemy(int(e_info[2]), int(e_info[3]), int(e_info[4]), f"resources/images/{e_info[1]}",
                                                              drops, self.assets_paths)

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
            if not filename.endswith(".map"):
                continue
            map_name = filename[:-4]
            print(map_name)
            map = arcade.SpriteList(use_spatial_hash=True)
            map_file = open("./resources/maps/"+filename)
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
                        map.append(assets.Path(rot, "./resources/images/path.png", (j, i)))
                    j += 1
                i += 1

            self.availables_maps[map_name] = map

    def load_map(self, map_name):
        map = self.availables_maps[map_name]
        self.assets_paths = map

    def on_draw(self):
        arcade.start_render()

        self.assets_paths.draw()
        self.assets_towers.draw()
        self.assets_enemies.draw()


def main():
    td = TowerDefence()
    td.load_map("0")
    arcade.run()


if __name__ == "__main__":
    main()
