import arcade
import arcade.gui
from typing import List, Dict, Optional, Tuple

import main
from assets.towers import Tower

SCALE = 4


class ShopItem(arcade.gui.UIImageButton):

    def __init__(self, name: str, img: str, tower: Tower, price: int, description: str, shop: "Shop", scale: float = 2):
        super().__init__(arcade.load_texture(img), scale=scale)
        self.tower: Tower = tower
        self.price: int = price
        self.name: str = name
        self.description: str = description
        self.shop: "Shop" = shop

    def on_press(self):
        self.shop.on_press(self)

    def on_hover(self):
        self.shop.game.info_ui.info_tower = self


class Shop:

    def __init__(self, tower_infos: List[Dict[str, any]], pos: tuple,
                 game: main.TowerDefenseMap,
                 scale: float = 2
                 ):
        self.towers: List[ShopItem] = [ShopItem(scale=SCALE / 2, **kwargs, shop=self) for kwargs in tower_infos]
        self.shop_sprites: Dict[arcade.Sprite, Tower] = {}
        self.sprites: arcade.SpriteList = arcade.SpriteList()
        self.scale: float = scale
        self.pos: tuple = pos
        self.width: int = 1280
        self.offset: tuple = (78, 78)
        self.cur_price: int = 0
        self.shop_background = arcade.Sprite("./resources/images/shop.png")
        self.hitbox_color_not_placeable = arcade.csscolor.RED
        self.hitbox_color_placeable = arcade.csscolor.GREEN

        self.game = game
        # self.path_list = path_list
        # self.tower_list = tower_list

        self.hold_object: Optional[Tower] = None

        self.setup()

    def setup(self):
        spacing = 112
        total_offset = self.offset[0]
        for spr in self.towers:
            spr.position = (total_offset, self.pos[1])
            self.game.ui_manager.add_ui_element(spr)

            self.sprites.append(spr)

            total_offset += spacing

        self.shop_background.position = self.pos
        self.game.add_sprite(self.shop_background, True)

    def draw(self, **kwargs):
        self.shop_background.draw()
        # arcade.draw_rectangle_filled(self.pos[0], self.pos[1], self.width,
        #                              self.offset[1] * 2, (0, 127, 0))
        # self.sprites.draw(**kwargs)

    def on_press(self, obj: ShopItem):
        if obj.price > self.game.data:
            self.game.info_ui.warn_text = "Not enough data to buy"
            return
        self.hold_object = obj.tower.clone()
        self.cur_price = obj.price
        self.hold_object.activated = False
        self.hold_object.selected = True
        self.game.add_sprite(self.hold_object)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.hold_object is None:
            return
        else:
            self.hold_object.position = x, y
            cols: list = self.hold_object.collides_with_list(self.game.assets_towers)
            cols.extend(self.hold_object.collides_with_list(self.game.assets_paths))
            if len(self.hold_object.collides_with_list(self.game.assets_solid)) > 0:
                self.game.assets_towers.remove(self.hold_object)
                self.game.assets_solid.remove(self.hold_object)
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
            cols: list = self.hold_object.collides_with_list(self.game.assets_solid)
            self.hold_object.placeable = len(cols) == 0
            # if len(cols) > 0:
                # print("not placeable")
            #     self.hold_object.hitbox_color = self.hitbox_color_not_placeable
            # else:
                # print("placeable")
            #     self.hold_object.hitbox_color = self.hitbox_color_placeable


class StartWaveButton(arcade.gui.UIImageButton):

    def __init__(self, game: main.TowerDefenseMap):
        super().__init__(
            arcade.load_texture("./resources/images/start_wave_button.png"),
            arcade.load_texture("./resources/images/start_wave_button_hover.png"),
            arcade.load_texture("./resources/images/start_wave_button_click.png")
            )
        self.game = game

    def on_release(self):
        # super().on_release()
        self.game.start_wave()

    def update(self):
        super().update()
        self.set_proper_texture()

    def on_wave_finish(self):
        super().on_release()


class SpeedButtons(arcade.gui.UIImageButton):

    def __init__(self, speed: str, game: main.TowerDefenseMap, buttons: List["SpeedButtons"]):
        super().__init__(
            arcade.load_texture(f"./resources/images/button_speed_{speed}.png"),
            arcade.load_texture(f"./resources/images/button_speed_{speed}_hover.png"),
            arcade.load_texture(f"./resources/images/button_speed_{speed}_active.png"),
        )
        self.game = game
        self.speed: str = speed
        self.buttons = buttons

    def on_release(self):
        for button in self.buttons:
            if button is not self:
                button.deactivate()
        self.game.window.set_update_rate(1/eval(f"main.TPS_{self.speed.upper()}"))

    def deactivate(self):
        super().on_release()


class EscapeButton(main.StartButton):

    def __init__(self, window: arcade.Window, tdm: main.TowerDefenseMap):
        super().__init__("button_pause", None, window)
        self.tdm = tdm

    def on_press(self):
        self.window.show_view(main.EscapeScreen(self.tdm))


class InfoUI:

    def __init__(self, game: main.TowerDefenseMap):
        self.game = game
        self.size = (256, main.WINDOW_HEIGHT)
        self.topleft_pos = (main.WINDOW_WIDTH - self.size[0], main.WINDOW_HEIGHT - 118)
        self.center_pos = (main.WINDOW_WIDTH - (self.size[0] / 2), (main.WINDOW_HEIGHT / 2)-60)
        self.sprites = arcade.SpriteList()
        self.stats_box_topleft: tuple = (0, 0)
        self.info_box_topleft: tuple = (0, 0)
        self.button_box_topleft: tuple = (0, 0)
        self.margin = 11
        self.middle = self.topleft_pos[0] + self.size[0]/2
        self.background: arcade.Sprite = arcade.Sprite("./resources/images/info.png")
        self.background.position = self.center_pos
        self.game.add_sprite(self.background, True)
        self.sprites.append(self.background)

        self.sw_button = StartWaveButton(self.game)
        self.pause_button = EscapeButton(self.game.window, self.game)

        self.speed_buttons: List[SpeedButtons] = []

        self._warn_text: str = ""
        self._warn_age = 0
        self._age_warn = False

        self.info_tower: Optional[ShopItem] = None

        self.default_offset: Tuple[int, int] = (16, 48)
        self.setup()

    def _get_warn_text(self):
        return self._warn_text

    def _set_warn_text(self, text: str):
        self._warn_text = text
        self._warn_age = 0
        self._age_warn = True

    warn_text = property(_get_warn_text, _set_warn_text)

    def setup(self):
        self.stats_box_topleft = self.topleft_pos[0] + self.margin, self.topleft_pos[1] + 12

        self.info_box_topleft = self.topleft_pos[0] + self.margin, self.topleft_pos[1] - 132

        self.button_box_topleft = self.topleft_pos[0] + self.margin, self.info_box_topleft[1] - 247

        self.sw_button.position = self.middle + 75, self.button_box_topleft[1] - 175
        self.sprites.append(self.sw_button)
        self.game.ui_manager.add_ui_element(self.sw_button)

        self.pause_button.position = self.middle - 75, self.button_box_topleft[1] - 175
        self.sprites.append(self.pause_button)
        self.game.ui_manager.add_ui_element(self.pause_button)

        x = 24
        i = 1
        first_button = True
        for speed in ["normal", "fast", "fastest"]:
            b = SpeedButtons(speed, self.game, self.speed_buttons)
            if first_button:
                b.on_press()
                first_button = False
            b.position = self.button_box_topleft[0] + x, self.button_box_topleft[1] - self.default_offset[1]/2
            self.speed_buttons.append(b)
            self.game.ui_manager.add_ui_element(b)
            i += 0.8
            x += 32*i

        # self.sprites.append(self.data_text)
        # self.sprites.append(self.lives_text)

    def update(self):
        self.sw_button.update()
        if self._age_warn:
            self._warn_age += 1
            if self._warn_age > 100:
                self._warn_text = ""
                self._age_warn = False

    def draw(self, **kwargs):
        # arcade.draw_rectangle_filled(self.center_pos[0], self.center_pos[1], self.size[0], self.size[1], (0, 0, 128))
        self.background.draw()
        # arcade.draw_point(self.info_box_topleft[0], self.info_box_topleft[1], (255, 255, 255), 2)
        # arcade.draw_point(self.stats_box_topleft[0], self.stats_box_topleft[1], (255, 255, 255), 2)
        # arcade.draw_point(self.button_box_topleft[0], self.button_box_topleft[1], (255, 255, 255), 2)

        arcade.draw_text(f"Data: {self.game.data}",
                         self.stats_box_topleft[0] + self.default_offset[0],
                         self.stats_box_topleft[1] - self.default_offset[1],
                         (255, 255, 255),
                         font_name="./resources/fonts/Welbut",
                         font_size=5 * SCALE,
                         anchor_x="left",
                         )

        arcade.draw_text(f"Lives: {self.game.lives}",
                         self.stats_box_topleft[0] + self.default_offset[0],
                         self.stats_box_topleft[1] - (self.default_offset[1] * 1.7),
                         (255, 255, 255),
                         font_name="./resources/fonts/Welbut",
                         font_size=5 * SCALE,
                         anchor_x="left"
                         )
        arcade.draw_text(f"Wave: {self.game.wave_no}",
                         self.stats_box_topleft[0] + self.default_offset[0],
                         self.stats_box_topleft[1] - (self.default_offset[1] * 2.4),
                         (255, 255, 255),
                         font_name="./resources/fonts/Welbut",
                         font_size=5 * SCALE,
                         anchor_x="left"
                         )
        arcade.draw_text(self.warn_text,
                         self.info_box_topleft[0] + self.default_offset[0],
                         self.info_box_topleft[1] - (self.default_offset[1] + 175),
                         (255, 0, 0),
                         font_name="./resources/fonts/Welbut",
                         font_size=3 * SCALE,
                         anchor_x="left"
                         )

        if self.info_tower is not None:
            arcade.draw_text(self.info_tower.name,
                             self.middle,
                             self.info_box_topleft[1] - self.default_offset[1],
                             (255, 255, 255),
                             font_name="./resources/fonts/Welbut",
                             font_size=5 * SCALE,
                             anchor_x="center"
                             )
            arcade.draw_text(self.info_tower.description,
                             self.middle,
                             self.info_box_topleft[1] - (self.default_offset[1] * 2),
                             (255, 255, 255),
                             font_name="./resources/fonts/Welbut",
                             font_size=4 * SCALE,
                             width=192,
                             anchor_x="center"
                             )
            affordable = self.info_tower.price <= self.game.data
            arcade.draw_text(str(self.info_tower.price) + " Data",
                             self.middle,
                             self.info_box_topleft[1] - (self.default_offset[1] * 3),
                             ((not affordable)*255, affordable*255, 0),
                             font_name="./resources/fonts/Welbut",
                             font_size=3 * SCALE,
                             anchor_x="center"
                             )
