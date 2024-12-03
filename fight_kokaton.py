import os
import random
import sys
import time
import pygame as pg

WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 爆弾の個数
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # スクリプト実行ディレクトリに変更


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    delta = {pg.K_UP: (0, -5), pg.K_DOWN: (0, +5), pg.K_LEFT: (-5, 0), pg.K_RIGHT: (+5, 0)}
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)
    imgs = {
        (+5, 0): img,
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),
        (-5, 0): img0,
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),
    }

    def __init__(self, xy: tuple[int, int]):
        self.img = __class__.imgs[(+5, 0)]
        self.rct = self.img.get_rect()
        self.rct.center = xy

    def change_img(self, num: int, screen: pg.Surface):
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
        screen.blit(self.img, self.rct)


class Beam:
    def __init__(self, bird: Bird):
        self.img = pg.image.load("fig/beam.png")
        self.rct = self.img.get_rect()
        self.rct.centery = bird.rct.centery
        self.rct.left = bird.rct.right
        self.vx = +10

    def update(self, screen: pg.Surface):
        self.rct.move_ip(self.vx, 0)
        if check_bound(self.rct) == (True, True):
            screen.blit(self.img, self.rct)


class Bomb:
    def __init__(self, color: tuple[int, int, int], rad: int):
        self.img = pg.Surface((2 * rad, 2 * rad), pg.SRCALPHA)
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = random.choice([-5, 5]), random.choice([-5, 5])

    def update(self, screen: pg.Surface):
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Score:
    """
    ゲームスコアを管理するクラス
    """
    def __init__(self, font_size=30, font_color=(0, 0, 255)):
        """
        スコア表示用フォントと初期値を設定
        """
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", font_size)
        self.color = font_color
        self.score = 0  # スコアの初期値
        self.img = self.font.render(f"スコア: {self.score}", True, self.color)
        self.rect = self.img.get_rect()
        self.rect.topleft = (10, 10)  # 左上に表示

    def add_score(self, points):
        """
        スコアを加算する
        引数 points: 加算するポイント
        """
        self.score += points
        self.update_img()

    def update_img(self):
        """
        スコアの表示用Surfaceを更新
        """
        self.img = self.font.render(f"スコア: {self.score}", True, self.color)

    def draw(self, screen):
        """
        スコアを画面に描画
        引数 screen: ゲーム画面
        """
        screen.blit(self.img, self.rect)


def main():
    pg.init()
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    score = Score()  # スコアクラスのインスタンス生成
    beam = None
    clock = pg.time.Clock()
    beams = []

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.append(Beam(bird))

        screen.blit(bg_img, [0, 0])

        # 衝突判定
        for bomb in bombs[:]:
            if bird.rct.colliderect(bomb.rct):
                bird.change_img(8, screen)
                font = pg.font.Font(None, 80)
                text = font.render("Game Over", True, (255, 0, 0))
                screen.blit(text, [WIDTH // 2 - 150, HEIGHT // 2])
                pg.display.update()
                time.sleep(2)
                return

        for i, bomb in enumerate(bombs):
            if beam is not None and beam.rct.colliderect(bomb.rct):
                # ビームが爆弾に当たった場合
                beam = None
                bombs[i] = None  # 爆弾を消去
                bird.change_img(6, screen)
                score.add_score(1)  # スコアを1加算
                pg.display.update()
                
        # ビームと爆弾の衝突判定
        for beam in beams[:]:
            for bomb in bombs[:]:
                if beam.rct.colliderect(bomb.rct):
                    beams.remove(beam)
                    bombs.remove(bomb)
                    break

        # 更新処理
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)

        for bomb in bombs:
            bomb.update(screen)
        for beam in beams[:]:
            beam.update(screen)      
        # スコアを描画
        score.draw(screen)
        pg.display.update()
        clock.tick(50)


if __name__ == "__main__":
    main()
    pg.quit()
    sys.exit()
