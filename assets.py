import arcade


class Tower(arcade.Sprite):

    def update(self):
        pass


class Path(arcade.Sprite):

    def __init__(self, rot, sprite):
        super().__init__(sprite)
        self.rot = rot
        self.turn_right(rot*90)

    def update(self):
        pass


class Enemy(arcade.Sprite):

    def __init__(self, hp, speed, dmg, sprite, drops, path_list):
        super().__init__(sprite, hit_box_algorithm="Detailed")
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

    def kill(self):

        super().kill()

    def clone(self):
        return Enemy(self.hp, self.speed, self.dmg, self.drops, self.paths)


class Bullet(arcade.Sprite):

    def __init__(self, speed, dmg, rot, sprite, enemy_list, pierce=1):
        super().__init__(sprite, hit_box_algorithm="Detailed")
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
