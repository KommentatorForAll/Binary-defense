import arcade
import assets


class TowerDefence(arcade.Window):

    def __init__(self):
        super().__init__(1920, 1080, "Binary Defence")

        arcade.set_background_color((0, 0, 0))

        # self.assets_all = None
        self.assets_paths = None
        self.assets_enemies = None
        self.assets_towers = None

        self.availables_enemies = None

    def setup(self):
        # self.assets_all = arcade.SpriteList()
        self.assets_paths = arcade.SpriteList(use_spatial_hash=True)
        self.assets_enemies = arcade.SpriteList()
        self.assets_towers = arcade.SpriteList(use_spatial_hash=True)

        self.availables_enemies = {}

    def load_availables(self):

        # Enemies
        enemy_file = open("./files/infos/enemies.txt")
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
            self.availables_enemies[e_info[0]] = assets.Enemy(int(e_info[2]), int(e_info[3]), int(e_info[4]), e_info[1],
                                                              drops, self.assets_paths)

        enemy_file.close()

        # Towers
        tower_file = open("./files/infos/towers.txt")
        towers = tower_file.read().split("\n")
        for tower in towers:
            if tower[0] == "#":
                continue
            t_info = tower.split(" ")


    def on_draw(self):
        arcade.start_render()


def main():
    td = TowerDefence()
    arcade.run()


if __name__ == "__main__":
    main()
