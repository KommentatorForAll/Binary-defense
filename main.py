import os
from typing import Dict, Optional

import arcade
from arcade.gui import UIManager
import assets
from pyglet.gl import GL_NEAREST

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_NAME = "Binary Defence"

TPS_NORMAL = 40
TPS_FAST = 100
TPS_FASTEST = 150


class TowerDefenceMap(arcade.View):

    def __init__(self):
        super().__init__()

        arcade.set_background_color((0, 0, 0))
        self.ui_manager = UIManager()

        # self.assets_all = arcade.SpriteList()
        self.assets_paths: arcade.SpriteList = arcade.SpriteList(use_spatial_hash=True)
        self.assets_enemies: arcade.SpriteList = arcade.SpriteList()
        self.assets_towers: arcade.SpriteList = arcade.SpriteList(use_spatial_hash=True)
        self.assets_solid: arcade.SpriteList = arcade.SpriteList(use_spatial_hash=True)

        self.availables_enemies: Dict[str, assets.enemies.Enemy] = {}
        self.availables_maps: Dict[str, assets.maps.Map] = {}
        self.availables_waves = []

        self.map: Optional[assets.maps.Map] = None
        self.wave: Optional[assets.maps.Wave] = None
        self._wave_active: bool = False

        self.shop: assets.ui.Shop = None
        self.info_ui: assets.ui.InfoUI = assets.ui.InfoUI(self)

        self._current_tps = TPS_NORMAL

        self.data = 0
        self._lives = 0
        self.wave_no = 0

        self.setup()

    def _get_lives(self):
        return self._lives

    def _set_lives(self, amount):
        self._lives = amount
        if amount <= 0:
            print("you died")
            print("move to endscreen")
            return

    lives = property(_get_lives, _set_lives)

    def _get_wave_active(self):
        return self._wave_active

    def _set_wave_active(self, is_active: bool):
        self._wave_active = is_active
        if not is_active:
            self.info_ui.sw_button.on_wave_finish()

    wave_active = property(_get_wave_active, _set_wave_active)

    def _set_cur_tps(self, tps):
        self.window.set_update_rate(1 / self._current_tps)
        self._current_tps = tps

    def _get_cur_tps(self):
        return self._current_tps

    current_tps = property(_get_cur_tps, _set_cur_tps)

    def setup(self):
        # self.assets_all = arcade.SpriteList()

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
            length = len(e_info)
            if length > 5:
                i = 5
                while i < length:
                    drops[e_info[i]] = int(e_info[i + 1])
                    i += 2
            self.availables_enemies[e_info[0]] = assets.enemies.Enemy(int(e_info[2]), int(e_info[3]), int(e_info[4]),
                                                                      f"resources/images/{e_info[1]}", drops,
                                                                      self.availables_enemies, self, None)

        enemy_file.close()

        # Waves
        wave_file = open("./resources/infos/waves.txt")
        waves = wave_file.read().split("\n")
        for wave in waves:
            if wave[0] == '#':
                continue
            w_info = wave.split(" ")
            enemies = []
            for i in range(0, len(w_info), 3):
                enemies.append(
                    {
                        "enemy": self.availables_enemies[w_info[i]],
                        "delay": int(w_info[i + 1]),
                        "cnt": int(w_info[i + 2])
                    }
                )
            self.availables_waves.append(enemies)

        wave_file.close()

        print(self.availables_waves)

        # Towers
        tower_file = open("resources/infos/towers.txt")
        towers_data = tower_file.read().split("\n")
        towers = []
        for tower in towers_data:
            if tower[0] == "#":
                continue
            info = {}
            t_info = tower.split(" ")
            info["name"] = t_info[0]
            info["tower"] = eval(f"assets.towers.{t_info[2]}(self.assets_enemies)")
            info["description"] = " ".join(t_info[4:])
            info["price"] = int(t_info[3])
            info["img"] = t_info[1]
            towers.append(info)

        # print(towers)

        self.shop = assets.ui.Shop(
            towers,
            # {
            #    "./resources/images/firewall.png": assets.Firewall(self.assets_enemies),
            #    "./resources/images/proxy.png": assets.Proxy(self.assets_enemies),
            #    "./resources/images/clam_tk.png": assets.Clam(self.assets_enemies)
            # },
            (
                WINDOW_WIDTH / 2,
                WINDOW_HEIGHT - 54
            ),
            self
        )
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
            self.availables_maps[map_name] = assets.maps.Map(**kwargs)
            # self.availables_maps[map_name] = map

    def add_sprite(self, spr: arcade.Sprite, solid=False):
        if isinstance(spr, assets.towers.Tower):
            self.assets_towers.append(spr)
            self.assets_solid.append(spr)
        elif isinstance(spr, assets.enemies.Enemy):
            self.assets_enemies.append(spr)
        elif solid:
            self.assets_solid.append(spr)

    def load_map(self, map_name: str):
        self.map = self.availables_maps[map_name]
        self.assets_paths = self.map.map
        self.assets_solid.extend(self.assets_paths)
        # self.assets_enemies.append(self.map.spawn(self.availables_enemies["enemy_10"]))
        # f = assets.Clam(self.assets_enemies)
        # self.assets_towers.append(f)
        # f.center_x = 256
        # f.center_y = 400
        self.data = int(self.map.data)
        self.lives = int(self.map.lives)

    def start_wave(self):
        if self.wave_active:
            return
        self.wave = assets.maps.Wave(self.availables_waves[self.wave_no], self.map, self)
        self.wave_no += 1
        self.wave_active = True

    def finish_wave(self):
        self.wave = None

    def on_update(self, delta_time: float):
        self.assets_paths.update()
        self.assets_enemies.update()
        self.assets_towers.update()
        self.info_ui.update()
        if self.wave is not None:
            self.wave.update()
        if self.wave_active:
            if len(self.assets_enemies) == 0:
                self.wave_active = False
                self.data += 100

    def on_draw(self):
        arcade.start_render()

        self.assets_paths.draw(filter=GL_NEAREST)
        self.assets_towers.draw(filter=GL_NEAREST)
        for tower in self.assets_towers:
            tower.draw()
        # self.assets_towers.draw_hit_boxes((255, 0, 0), 2)
        self.assets_enemies.draw(filter=GL_NEAREST)

        self.info_ui.draw(filter=GL_NEAREST)

        self.shop.draw(filter=GL_NEAREST)

    def update(self, delta_time):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        # self.shop.on_mouse_press(x, y, button, modifiers)
        pass

    def on_mouse_release(self, x, y, button, modifiers):
        self.shop.on_mouse_release(x, y, button, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        self.shop.on_mouse_drag(x, y, dx, dy, button, modifiers)


class GameWindow(arcade.Window):

    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_NAME)
        self.set_update_rate(1 / TPS_NORMAL)

        game_map = TowerDefenceMap()
        self.show_view(game_map)
        game_map.load_map("1")


def main():
    GameWindow()
    arcade.run()


if __name__ == "__main__":
    main()
