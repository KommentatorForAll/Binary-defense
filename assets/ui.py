import arcade
from typing import List, Dict, Optional, Tuple

import main
from assets.towers import Tower

SCALE = 4


class ShopItem(arcade.Sprite):

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)
        super().__init__(kwargs["img"], scale=kwargs["scale"] if kwargs.keys().__contains__("scale") else 1)
        self.tower: Tower = self.tower
        self.price: int = self.price
        self.name: str = self.name
        self.description: str = self.description


class Shop:

    def __init__(self, tower_infos: List[Dict[str, any]], pos: tuple,
                 game: main.TowerDefenceMap,
                 scale: float = 2
                 ):
        self.towers: List[ShopItem] = [ShopItem(scale=SCALE / 2, **kwargs) for kwargs in tower_infos]
        self.shop_sprites: Dict[arcade.Sprite, Tower] = {}
        self.sprites: arcade.SpriteList = arcade.SpriteList()
        self.scale: float = scale
        self.pos: tuple = pos
        self.width: int = 0
        self.offset: tuple = (50, 50)
        self.cur_price: int = 0
        self.hitbox_color_not_placeable = arcade.csscolor.RED
        self.hitbox_color_placeable = arcade.csscolor.GREEN

        self.game = game
        # self.path_list = path_list
        # self.tower_list = tower_list

        self.hold_object: Optional[Tower] = None

        self.col_checker: arcade.Sprite = arcade.SpriteCircle(4, (255, 0, 0))

        self.setup()

    def setup(self):
        spacing = 75
        total_width = len(self.towers) * spacing + self.offset[1] * 2
        print(f"total width: {total_width}, pos: {self.pos}, offset: {self.offset}")
        i = self.pos[0] - total_width / 2 + self.offset[1]
        for spr in self.towers:
            spr.position = (i, self.pos[1])

            self.sprites.append(spr)

            i += spacing
        i -= spacing
        i += self.offset[0] * 2
        self.width = total_width

    def draw(self, **kwargs):
        arcade.draw_rectangle_filled(self.pos[0], self.pos[1], self.width,
                                     self.offset[1] * 2, (0, 127, 0))
        self.sprites.draw(**kwargs)

    def on_mouse_press(self, x, y, button, modifiers):
        self.col_checker.position = x, y
        clicked_sprites = self.col_checker.collides_with_list(self.sprites)
        if len(clicked_sprites) != 0:
            print(f"clicked on {clicked_sprites[0]}")
            obj: ShopItem = clicked_sprites[0]
            self.game.info_ui.info_tower = obj
            if obj.price > self.game.data:
                self.game.info_ui.warn_text = "Not enough data to buy"
                return
            self.hold_object = obj.tower.clone()
            self.cur_price = obj.price
            self.hold_object.activated = False
            self.hold_object.selected = True
            self.game.assets_towers.append(self.hold_object)
        else:
            print("didn't click on shop item")

    def on_mouse_release(self, x, y, button, modifiers):
        if self.hold_object is None:
            return
        else:
            self.hold_object.position = x, y
            cols: list = self.hold_object.collides_with_list(self.game.assets_towers)
            cols.extend(self.hold_object.collides_with_list(self.game.assets_paths))
            if len(cols) > 0:
                self.game.assets_towers.remove(self.hold_object)
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
            cols: list = self.hold_object.collides_with_list(self.game.assets_paths)
            cols.extend(self.hold_object.collides_with_list(self.game.assets_towers))
            if len(cols) > 0:
                # print("not placeable")
                self.hold_object.hitbox_color = self.hitbox_color_not_placeable
            else:
                # print("placeable")
                self.hold_object.hitbox_color = self.hitbox_color_placeable


class InfoUI:

    def __init__(self, game: main.TowerDefenceMap):
        self.game = game
        self.size = (250, main.WINDOW_HEIGHT)
        self.topleft_pos = (main.WINDOW_WIDTH - self.size[0], main.WINDOW_HEIGHT)
        self.center_pos = (main.WINDOW_WIDTH - (self.size[0] / 2), main.WINDOW_HEIGHT / 2)
        self.sprites = arcade.SpriteList()
        self.data_text: arcade.Sprite = arcade.Sprite("./resources/images/text_data.png", scale=SCALE)
        self.lives_text: arcade.Sprite = arcade.Sprite("./resources/images/text_lives.png", scale=SCALE)
        self._warn_text: str = ""
        self._warn_age = 0
        self._age_warn = False

        self.info_tower: Optional[ShopItem] = None

        self.default_offset: Tuple[int, int] = (20, 0)
        self.setup()

    def _get_warn_text(self):
        return self._warn_text

    def _set_warn_text(self, text: str):
        self._warn_text = text
        self._warn_age = 0
        self._age_warn = True

    warn_text = property(_get_warn_text, _set_warn_text)

    def setup(self):
        self.data_text.position = self.topleft_pos[0] + self.default_offset[0], self.topleft_pos[1] - 48

        self.lives_text.position = self.topleft_pos[0] + self.default_offset[0], self.topleft_pos[1] - 128

        # self.sprites.append(self.data_text)
        # self.sprites.append(self.lives_text)

    def update(self):
        if self._age_warn:
            self._warn_age += 1
            if self._warn_age > 100:
                self._warn_text = ""
                self._age_warn = False

    def draw(self, **kwargs):
        arcade.draw_rectangle_filled(self.center_pos[0], self.center_pos[1], self.size[0], self.size[1], (0, 0, 128))
        self.sprites.draw(**kwargs)

        arcade.draw_text(f"Data: {self.game.data}",
                         self.data_text.position[0],
                         self.data_text.position[1],
                         (0, 255, 0),
                         font_name="./resources/fonts/Welbut",
                         font_size=7 * SCALE,
                         anchor_x="left",
                         )

        arcade.draw_text(f"Lives: {self.game.lives}",
                         self.lives_text.position[0],
                         self.lives_text.position[1],
                         (0, 255, 0),
                         font_name="./resources/fonts/Welbut",
                         font_size=7 * SCALE,
                         anchor_x="left"
                         )

        arcade.draw_text(self.warn_text,
                         self.topleft_pos[0] + self.default_offset[0],
                         self.topleft_pos[1] - main.WINDOW_HEIGHT + 50,
                         (255, 0, 0),
                         font_name="./resources/fonts/Welbut",
                         font_size=3 * SCALE,
                         anchor_x="left"
                         )

        if self.info_tower is not None:
            arcade.draw_text(self.info_tower.name,
                             self.topleft_pos[0] + self.default_offset[0],
                             self.topleft_pos[1] - 230,
                             (255, 255, 255),
                             font_name="./resources/fonts/Welbut",
                             font_size=4 * SCALE,
                             anchor_x="left"
                             )
            arcade.draw_text(self.info_tower.description,
                             self.topleft_pos[0] + self.default_offset[0],
                             self.topleft_pos[1] - 256,
                             (255, 255, 255),
                             font_name="./resources/fonts/Welbut",
                             font_size=3 * SCALE,
                             anchor_x="left"
                             )
            affordable = self.info_tower.price <= self.game.data
            arcade.draw_text(str(self.info_tower.price) + " Data",
                             self.topleft_pos[0] + self.default_offset[0],
                             self.topleft_pos[1] - 330,
                             ((not affordable)*255, affordable*255, 0),
                             font_name="./resources/fonts/Welbut",
                             font_size=3 * SCALE,
                             anchor_x="left"
                             )
