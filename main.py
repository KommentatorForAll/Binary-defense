import os
import random
from typing import Dict, Optional, List

import arcade
import pyglet
from arcade.gui import UIManager
from pyglet.gl import GL_NEAREST

import assets
from map_creator import MapCreator, LoadMapButton

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_NAME = "Binary Defence"

SCALE = 4

TPS_NORMAL = 40
TPS_FAST = 100
TPS_FASTEST = 150


# GUI_STYLE = arcade.gui.UIStyle(
#     font="./resources/fonts/Welbut",
#     color=arcade.color.WHITE
# )
# arcade.gui.UIStyle.set_default_style(GUI_STYLE)


class StartButton(arcade.gui.UIImageButton):

    def __init__(self, name: str, switch_to, window: arcade.Window, **kwargs):
        super().__init__(
            arcade.load_texture(f"./resources/images/{name}.png"),
            arcade.load_texture(f"./resources/images/{name}_hover.png"),
            arcade.load_texture(f"./resources/images/{name}_press.png"),
            **kwargs
        )
        self.switch_to = switch_to
        self.window: arcade.Window = window

    def on_click(self):
        super().on_click()
        x = self.switch_to(self.window)
        self.window.show_view(x)
        # x.load_map(assets.maps.Map("1.map"))


class DeathScreen(arcade.View):

    def __init__(self, wave_no: int):
        super().__init__()

        self.ui_manager = arcade.gui.UIManager()
        self.sprites = arcade.SpriteList(use_spatial_hash=True)

        self.wave_no = wave_no

        self.button_return = StartButton("button_big_empty", TitleScreen, self.window, text="Main Menu")
        self.button_return.position = WINDOW_WIDTH/2, 128
        self.ui_manager.add_ui_element(self.button_return)

        self.death_text = arcade.Sprite("./resources/images/text_death.png", scale=SCALE * 3)
        self.death_text.position = WINDOW_WIDTH/2, WINDOW_HEIGHT - 128
        self.sprites.append(self.death_text)

    def on_draw(self):
        arcade.start_render()
        # self.ui_manager.on_draw()
        self.sprites.draw(filter=GL_NEAREST)

        arcade.draw_text(
            f"you made it to wave {self.wave_no}",
            WINDOW_WIDTH/2,
            256,
            (255, 0, 0),
            font_name="./resources/fonts/Welbut",
            font_size=20,
            anchor_x="center"
        )

    def on_hide_view(self):
        self.ui_manager.unregister_handlers()
        # self.ui_manager.disable()

    def on_show_view(self):
        # self.ui_manager.enable()
        pass


class ResumeButton(StartButton):

    def on_press(self):
        self.window.show_view(self.switch_to)


class QuitButton(StartButton):

    def __init__(self, es: "EscapeScreen", window: arcade.Window):
        super().__init__("button_big_empty", None, window, text="Quit")
        self.es = es

    def on_click(self):
        self.es.ui_manager.add_ui_element(self.es.really_quit_button)
        self.es.warning = "Confirm quit. You will loose all your progress"


class EscapeScreen(arcade.View):

    def __init__(self, tdm: "TowerDefenceMap"):
        super().__init__()
        self.tdm = tdm

        self.ui_manager = UIManager()

        self.button_resume = ResumeButton("button_big_empty", tdm, self.window, text="Resume")
        self.button_resume.position = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 128
        self.ui_manager.add_ui_element(self.button_resume)

        self.quit_button = QuitButton(self, self.window)
        self.quit_button.position = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2
        self.ui_manager.add_ui_element(self.quit_button)

        self.really_quit_button = StartButton("button_big_empty", TitleScreen, self.window, text="Really Quit")
        self.really_quit_button.position = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 128

        self.warning = "Game Paused"

    def on_draw(self):
        arcade.start_render()
        # self.ui_manager.on_draw()
        arcade.draw_text(
            self.warning,
            WINDOW_WIDTH / 2,
            WINDOW_HEIGHT / 2 + 275,
            (255, 0, 0),
            font_name="./resources/fonts/Welbut",
            font_size=28,
            anchor_x="center"
            )

    def on_hide_view(self):
        self.ui_manager.unregister_handlers()
        # self.ui_manager.disable()

    def on_show_view(self):
        # self.ui_manager.enable()
        pass


class TowerDefenceMap(arcade.View):
    """
    Class that hosts the main game.

    Attributes:
        :assets_paths: The list of paths, passed by the currently loaded Map
        :assets_enemies: All enemies, currently in the world
        :assets_towers: The currently placed towers
        :asstes_solid: A list of all sprites on which one is unable to place Towers ontop of
        :availables_enemies: A Dictionary of enemy names and an initial enemy instance
        :availables_waves: A list of waves, which get spawned when a button is pressed
        :map: The currently loaded map. Empty if None is loaded
        :wave: The current Wave. Empty if None is loaded
    """

    def __init__(self):
        super().__init__()

        arcade.set_background_color((0, 0, 0))
        self.ui_manager = UIManager(self.window, attatch_callbacks=False)

        # self.assets_all = arcade.SpriteList()
        self.assets_paths: arcade.SpriteList = arcade.SpriteList(use_spatial_hash=True)
        self.assets_enemies: arcade.SpriteList = arcade.SpriteList()
        self.assets_towers: arcade.SpriteList = arcade.SpriteList(use_spatial_hash=True)
        self.assets_solid: arcade.SpriteList = arcade.SpriteList(use_spatial_hash=True)

        self.availables_enemies: Dict[str, assets.enemies.Enemy] = {}
        self.availables_waves: List[assets.maps.Wave] = []

        self.map: Optional[assets.maps.Map] = None
        self.wave: Optional[assets.maps.Wave] = None
        self._wave_active: bool = False

        self.is_activated: bool = True

        self.shop: assets.ui.Shop = None
        self.info_ui: assets.ui.InfoUI = assets.ui.InfoUI(self)

        self._current_tps = TPS_NORMAL

        self.data = 0
        self._lives = 0
        self.wave_no = 0

        self.setup()

    def _get_lives(self) -> int:
        """

        Returns
        -------
        int
            The current amount of lives

        """
        return self._lives

    def _set_lives(self, amount: int):
        """

        Parameters
        ----------
        amount : int
            The new amount of lives

        Returns
        -------
        None.

        """
        self._lives = amount
        if amount <= 0:
            print("you died")
            print("move to endscreen")
            ds = DeathScreen(self.wave_no)
            self.window.show_view(ds)
            return

    lives = property(_get_lives, _set_lives)

    def _get_wave_active(self) -> bool:
        """

        Returns
        -------
        bool
            Checks if there is currently an active wave

        """
        return self._wave_active

    def _set_wave_active(self, is_active: bool) -> None:
        """

        Parameters
        ----------
        is_active : bool
            Activates or deactivates the current wave

        Returns
        -------
        None.

        """
        self._wave_active = is_active
        if not is_active:
            self.info_ui.sw_button.on_wave_finish()

    wave_active = property(_get_wave_active, _set_wave_active)

    def _set_cur_tps(self, tps: int):
        """

        Parameters
        ----------
        tps : int
            Sets the games tps (ticks per second)

        Returns
        -------
        None.

        """

        self.window.set_update_rate(1 / self._current_tps)
        self._current_tps = tps

    def _get_cur_tps(self) -> int:
        """


        Returns
        -------
        int
            The current tps of the game

        """
        return self._current_tps

    current_tps = property(_get_cur_tps, _set_cur_tps)

    def setup(self):
        # self.assets_all = arcade.SpriteList()

        self.load_availables()

    def load_availables(self):
        """
            Loads all available reources

        Returns
        -------
        None.

        """

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

    def add_sprite(self, spr: arcade.Sprite, solid: bool = False):
        """


        Parameters
        ----------
        spr : arcade.Sprite
            The spride to add
        solid : bool, optional
            If one is able to place towers on top(automatic for towers, enemies and paths). The default is False.

        Returns
        -------
        None.

        """
        if isinstance(spr, assets.towers.Tower):
            self.assets_towers.append(spr)
            self.assets_solid.append(spr)
        elif isinstance(spr, assets.enemies.Enemy):
            self.assets_enemies.append(spr)
        elif solid:
            self.assets_solid.append(spr)

    def load_map(self, map: "assets.maps.Map"):
        """
        Loads in a new map.

        Parameters
        ----------
        map : assets.maps.Map
            The map to load.

        Returns
        -------
        None.

        """
        self.map = map
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
        """
        Starts a wave

        Returns
        -------
        None.

        """
        if self.wave_active:
            return
        self.wave = assets.maps.Wave(self.availables_waves[self.wave_no], self.map, self)
        self.wave_no += 1
        self.wave_active = True

    def finish_wave(self):
        self.wave = None

    def on_update(self, delta_time: float):
        if not self.is_activated:
            return
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
        if not self.is_activated:
            return
        arcade.start_render()
        self.assets_paths.draw(filter=GL_NEAREST)
        for path in self.assets_paths:
            path.draw(filter=GL_NEAREST)
        self.assets_towers.draw(filter=GL_NEAREST)
        for tower in self.assets_towers:
            tower.draw(filter=GL_NEAREST)
        # self.assets_towers.draw_hit_boxes((255, 0, 0), 2)
        self.assets_enemies.draw(filter=GL_NEAREST)

        self.info_ui.draw(filter=GL_NEAREST)

        self.shop.draw(filter=GL_NEAREST)
        # self.ui_manager.on_draw()

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.window.show_view(EscapeScreen(self))

    def update(self, delta_time):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        # self.shop.on_mouse_press(x, y, button, modifiers)
        pass

    def on_mouse_release(self, x, y, button, modifiers):
        self.shop.on_mouse_release(x, y, button, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        self.shop.on_mouse_drag(x, y, dx, dy, button, modifiers)

    def on_show_view(self):
        #if not self.is_activated:
        print("regisadfasdfas")
        self.ui_manager.register_handlers()
        self.is_activated = True
        # self.ui_manager.enable()

    def on_hide_view(self):
        self.is_activated = False
        self.ui_manager.unregister_handlers()
        # self.ui_manager.disable()


class LoopingSprite(arcade.Sprite):

    def __init__(self, sprite, **kwargs):
        super().__init__(sprite, **kwargs)

    def update(self):
        super().update()
        if self.center_x > WINDOW_WIDTH:
            self.center_x = 0
        elif self.center_x < 0:
            self.center_x = WINDOW_WIDTH


class TitleScreen(arcade.View):

    def __init__(self, window: arcade.Window):
        super().__init__(window)
        self.ui_manager = UIManager(self.window, attatch_callbacks=False)

        self.sprites = arcade.SpriteList(use_spatial_hash=True)

        self.start_button = StartButton("button_start", LevelSelector, window)
        self.start_button.position = WINDOW_WIDTH / 2, WINDOW_HEIGHT - 450
        self.sprites.append(self.start_button)
        self.ui_manager.add_ui_element(self.start_button)

        self.title_sprite = arcade.Sprite("./resources/images/title_full.png", scale=6)
        self.title_sprite.position = WINDOW_WIDTH / 2, WINDOW_HEIGHT - 125
        self.sprites.append(self.title_sprite)

        self.bg_sprites = arcade.SpriteList()

        for i in range(random.randrange(5, 10)):
            spr = LoopingSprite(f"./resources/images/enemy_{random.randrange(2)}.png", scale=4)
            spr.position = random.randrange(WINDOW_WIDTH), random.randrange(WINDOW_HEIGHT)
            spr.forward(random.randrange(0, 12) - 6)
            self.bg_sprites.append(spr)

    def on_draw(self):
        arcade.start_render()
        self.bg_sprites.draw(filter=GL_NEAREST)
        self.sprites.draw(filter=GL_NEAREST)
        # self.ui_manager.on_draw()

    def on_update(self, delta_time: float):
        self.bg_sprites.update()

    def on_hide_view(self):
        self.ui_manager.unregister_handlers()
        # self.ui_manager.disable()

    def on_show_view(self):
        # self.ui_manager.enable()
        pass


class MapSelectButton(StartButton):

    def __init__(self, name: str, window: arcade.Window, map_name: str, **kwargs):
        super().__init__("button_empty", TowerDefenceMap, window, text=name, **kwargs)
        self.map = map_name

    def on_click(self):
        td = self.switch_to()
        self.window.show_view(td)
        td.load_map(assets.maps.Map(self.map))


class LevelSelector(arcade.View):

    def __init__(self, window: arcade.Window):
        super().__init__(window)

        self.ui_manager = UIManager(self.window, attatch_callbacks=False)

        self.sprites = arcade.SpriteList(use_spatial_hash=True)

        self.button_back = StartButton("button_big_empty", TitleScreen, window, text="Back")
        self.button_back.position = WINDOW_WIDTH / 2, 64
        self.ui_manager.add_ui_element(self.button_back)

        self.button_creator = StartButton("button_big_empty", MapCreator, window, text="Create Map")
        self.button_creator.position = WINDOW_WIDTH - 128, 64
        self.ui_manager.add_ui_element(self.button_creator)

        self.availables_maps: List[str] = []

        self.text_levels = arcade.Sprite("./resources/images/text_levels.png", scale=SCALE * 2)
        self.text_levels.position = WINDOW_WIDTH / 2, WINDOW_HEIGHT - 128
        self.sprites.append(self.text_levels)

        self.button_load_map = LoadMapButton(self, self.window)
        self.button_load_map.position = 128, 64
        self.ui_manager.add_ui_element(self.button_load_map)

        self.bg_sprites = arcade.SpriteList()

        for i in range(random.randrange(5, 10)):
            spr = LoopingSprite(f"./resources/images/enemy_{random.randrange(2)}.png", scale=4)
            spr.position = random.randrange(WINDOW_WIDTH), random.randrange(WINDOW_HEIGHT)
            spr.forward(random.randrange(0, 12) - 6)
            self.bg_sprites.append(spr)

        # Maps
        for filename in os.listdir("resources/maps"):
            if not filename.endswith(".map"):
                continue
            map_name = filename[:-4]
            self.availables_maps.append(map_name)

        x, y = 128, WINDOW_HEIGHT - 256
        for name in self.availables_maps:
            spr = MapSelectButton(name, self.window, f"{name}.map")
            spr.position = x, y
            self.ui_manager.add_ui_element(spr)
            x += 128
            if x > WINDOW_WIDTH - 128:
                x = 128
                y += 128

    def on_draw(self):
        arcade.start_render()
        self.bg_sprites.draw(filter=GL_NEAREST)
        # self.ui_manager.on_draw()
        self.sprites.draw(filter=GL_NEAREST)

    def on_update(self, delta_time: float):
        self.bg_sprites.update()

    def on_hide_view(self):
        self.ui_manager.unregister_handlers()
        # self.ui_manager.disable()

    def on_show_view(self):
        # self.ui_manager.enable()
        pass


class GameWindow(arcade.Window):

    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_NAME)
        self.set_update_rate(1 / TPS_NORMAL)
        self.set_icon(pyglet.image.load("./resources/images/icon.png"))
        game_map = TitleScreen(self)
        self.show_view(game_map)
        self.bg_music = arcade.load_sound("./resources/sounds/data_stream_bg_music.mp3")
        self.bg_music.play(loop=True)
        # game_map.load_map("1")


def main():
    GameWindow()
    arcade.run()


if __name__ == "__main__":
    main()
