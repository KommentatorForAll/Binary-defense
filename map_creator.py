from typing import Tuple, List

import arcade
import arcade.gui
import numpy as np
from pyglet.gl import GL_NEAREST

import assets

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
SCALE = 4


# GUI_STYLE = arcade.gui.UIStyle()


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
        self.window.show_view(self.switch_to(self.window))


class SaveMapButton(StartButton):

    def __init__(self, window: arcade.Window, map_creator: "MapCreator"):
        super().__init__("button_big_empty", MapSaver, window, text="Save Map")
        self.map_creator = map_creator

    def on_click(self):
        self.window.show_view(self.switch_to(self.map_creator, self.window))


class MapCreator(arcade.View):

    def __init__(self, window: arcade.Window):
        super().__init__(window)

        self.sp_init = False
        self.start_point: Tuple[int, int] = (0, 0)
        self.current_endpoint: Tuple[int, int] = (0, 0)
        self.current_start_point: Tuple[int, int] = (0, 0)
        self.mouse_pos = (0, 0)
        self.first = True

        self.segments: List["assets.maps.Segment"] = []
        self.assets_paths: arcade.SpriteList = arcade.SpriteList(use_spatial_hash=True)

        self.ui_manager = arcade.gui.UIManager()

        self.save_button = SaveMapButton(self.window, self)
        self.save_button.position = WINDOW_WIDTH - 128, 64
        self.ui_manager.add_ui_element(self.save_button)

    def on_draw(self):
        arcade.start_render()
        self.assets_paths.draw(filter=GL_NEAREST)
        for path in self.assets_paths:
            path.draw(filter=GL_NEAREST)
        if self.sp_init:
            arcade.draw_line(self.current_start_point[0] * SCALE * 16 + 32,
                             self.current_start_point[1] * SCALE * 16 + 32,
                             self.mouse_pos[0] * SCALE * 16 + 32,
                             self.mouse_pos[1] * SCALE * 16 + 32,
                             (0, 255, 0),
                             4
                             )

    def on_hide_view(self):
        # self.ui_manager.unregister_handlers()
        self.ui_manager.disable()

    def on_show_view(self):
        self.ui_manager.enable()
        pass

    def on_update(self, delta_time: float):
        pass

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        r_pnt = max(min(round(x / (SCALE * 16)), 15), 0), max(min(round(y / (SCALE * 16)), 7), 0)
        self.mouse_pos = r_pnt
        if not self.sp_init:
            self.start_point = r_pnt
            self.current_start_point = r_pnt
            self.sp_init = True
            return
        dx, dy = r_pnt[0] - self.current_start_point[0], r_pnt[1] - self.current_start_point[1]
        is_horizontal = abs(dx) >= abs(dy)
        r_pnt = r_pnt[0] if is_horizontal else self.current_start_point[0], \
                r_pnt[1] if not is_horizontal else self.current_start_point[1]
        dx = dx * is_horizontal
        dy = dy * (not is_horizontal)
        d = dx + dy

        abs_dx = np.sign(dx)
        abs_dy = np.sign(dy)

        if dx != 0:
            direction = 1 if dx > 0 else 3
        else:
            direction = 0 if dy > 0 else 2

        self.segments.append(assets.maps.Segment(direction, d))

        for i in range(abs(d)):
            self.assets_paths.append(
                assets.maps.Path(
                    direction,
                    (
                        self.current_start_point[0] + (abs_dx * i),
                        self.current_start_point[1] + (abs_dy * i)
                    ),
                    's' if self.first else None
                )
            )
            self.first = False

        self.current_start_point = r_pnt[0], r_pnt[1]

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        if not self.sp_init:
            return
        r_pnt = max(min(round(x / (SCALE * 16)), 15), 0), max(min(round(y / (SCALE * 16)), 7), 0)
        dx, dy = [sum((a, -b)) for a, b in zip(r_pnt, self.current_start_point)]
        is_horizontal = abs(dx) >= abs(dy)
        r_pnt = r_pnt[0] if is_horizontal else self.current_start_point[0], \
                r_pnt[1] if not is_horizontal else self.current_start_point[1]

        self.mouse_pos = r_pnt


class MapSaver(arcade.View):

    def __init__(self, map_creator: MapCreator, window: arcade.Window):
        super().__init__(window)
        self.map_creator = map_creator
        self.ui_manager = arcade.gui.UIManager()

        self.map_name_tf = arcade.gui.UIInputBox(width=256)
        self.map_name_tf.position = WINDOW_WIDTH / 2, WINDOW_HEIGHT - 128
        self.ui_manager.add_ui_element(self.map_name_tf)

        self.amount_lives_tf = arcade.gui.UIInputBox(text="100", width=256)
        self.amount_lives_tf.position = WINDOW_WIDTH / 2, WINDOW_HEIGHT - 256
        self.ui_manager.add_ui_element(self.amount_lives_tf)

        self.amount_data_tf = arcade.gui.UIInputBox(text="300", width=256)
        self.amount_data_tf.position = WINDOW_WIDTH / 2, WINDOW_HEIGHT - 384
        self.ui_manager.add_ui_element(self.amount_data_tf)

        self.map_name_lb = arcade.gui.UILabel(text="Map name", width=256)
        self.map_name_lb.position = WINDOW_WIDTH / 2, WINDOW_HEIGHT - 64
        self.ui_manager.add_ui_element(self.map_name_lb)

        self.amount_lives_lb = arcade.gui.UILabel(text="Start Lives", width=256)
        self.amount_lives_lb.position = WINDOW_WIDTH / 2, WINDOW_HEIGHT - 192
        self.ui_manager.add_ui_element(self.amount_lives_lb)

        self.amount_data_lb = arcade.gui.UILabel(text="Start Data", width=256)
        self.amount_data_lb.position = WINDOW_WIDTH / 2, WINDOW_HEIGHT - 320
        self.ui_manager.add_ui_element(self.amount_data_lb)

    def on_draw(self):
        arcade.start_render()

    def on_hide_view(self):
        # self.ui_manager.unregister_handlers()
        self.ui_manager.disable()

    def on_show_view(self):
        self.ui_manager.enable()
        pass
