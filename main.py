import pygame
from pygame.locals import *
import sys
import os
import random

SCR_RECT = Rect(0, 0, 640, 480)
GS = 32
DOWN,LEFT,RIGHT,UP = 0,1,2,3
STOP, MOVE = 0, 1  # 移動タイプ
PROB_MOVE = 0.005  # 移動確率

def main():
    pygame.init()
    screen = pygame.display.set_mode(SCR_RECT.size)
    pygame.display.set_caption(u"RPG")
    # キャラクターイメージをロード
    Character.images["player"] = split_image(load_image("player.png"))
    Character.images["king"] = split_image(load_image("king.png"))
    Character.images["minister"] = split_image(load_image("minister.png"))
    Character.images["soldier"] = split_image(load_image("soldier.png"))
    # マップチップをロード
    Map.images[0] = load_image("grass.png") # 草地
    Map.images[1] = load_image("water.png")  # 水
    Map.images[2] = load_image("forest.png") # 森
    Map.images[3] = load_image("hill.png")   # 丘
    Map.images[4] = load_image("mountain.png")  # 山
    # マップとプレイヤーを作成
    map = Map("test1")
    player = Player("player", (1,1), DOWN)
    # キャラクター作成
    king = Character("king", (2,1), DOWN, STOP)
    minister = Character("minister", (3,1), DOWN, MOVE)
    soldier = Character("soldier", (4,1), DOWN, MOVE)
    # キャラクターをマップに追加
    map.add_chara(player)
    map.add_chara(king)
    map.add_chara(minister)
    map.add_chara(soldier)
    clock = pygame.time.Clock()
    while True:
        clock.tick(60)
        map.update()
        offset = calc_offset(player)
        map.draw(screen, offset)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == QUIT:
                sys.exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                sys.exit()

def calc_offset(player):
    """オフセットを計算する"""
    offsetx = player.rect.topleft[0] - SCR_RECT.width//2
    offsety = player.rect.topleft[1] - SCR_RECT.height//2
    return offsetx, offsety

def load_image(filename, colorkey=None):
    current_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
    # parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
    file = os.path.join(current_dir, 'img', filename)
    try:
        surface = pygame.image.load(file)
    except pygame.error:
        raise SystemExit('Could not load image "%s" %s'%(file, pygame.get_error()))
    surface = surface.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = surface.get_at((0,0))
        surface.set_colorkey(colorkey, RLEACCEL)
    return surface

def split_image(image):
    """128x128のキャラクターイメージを32x32の16枚のイメージに分割
    分割したイメージを格納したリストを返す"""
    imageList = []
    for i in range(0, 128, GS):
        for j in range(0, 128, GS):
            surface = pygame.Surface((GS,GS))
            surface.blit(image, (0,0), (j,i,GS,GS))
            surface.set_colorkey(surface.get_at((0,0)), RLEACCEL)
            surface.convert()
            imageList.append(surface)
    return imageList

class Map:
    images = [None] * 256  # マップチップ（番号->イメージ）
    def __init__(self, name):
        self.name = name
        self.row = -1 # 行数
        self.col = -1 # 列数
        self.map = [] # マップデータ(2次元リスト)
        self.charas = []  # マップにいるキャラクターリスト
        self.load()
    def add_chara(self, chara):
        """キャラクターをマップに追加する"""
        self.charas.append(chara)
    def update(self):
        """マップの更新"""
        # マップにいるキャラクターの更新
        for chara in self.charas:
            chara.update(self)  # mapを渡す
    def load(self):
        """ファイルからマップをロード"""
        file = os.path.join("map", self.name + ".map")
        # テキスト形式のマップを読み込む
        fp = open(file)
        lines = fp.readlines()  # ファイル全体を行単位で読み込む
        row_str, col_str = lines[0].split()  # 行数と列数
        self.row, self.col = int(row_str), int(col_str)  # int型に変換
        self.default = int(lines[1])  # デフォルト値
        for line in lines[2:]:
            line = line.rstrip()  # 改行除去
            self.map.append([int(x) for x in list(line)])
        fp.close()
    def draw(self, screen, offset):
        """マップを描画する"""
        offsetx, offsety = offset
        # マップの描画範囲を計算
        startx = offsetx // GS
        endx = startx + SCR_RECT.width//GS + 1
        starty = offsety // GS
        endy = starty + SCR_RECT.height//GS + 1
        # マップの描画
        for y in range(starty, endy):
            for x in range(startx, endx):
                # マップの範囲外はデフォルトイメージで描画
                # この条件がないとマップの端に行くとエラー発生
                if x < 0 or y < 0 or x > self.col-1 or y > self.row-1:
                    screen.blit(self.images[self.default], (x*GS-offsetx,y*GS-offsety))
                else:
                    screen.blit(self.images[self.map[y][x]], (x*GS-offsetx,y*GS-offsety))
        # このマップにいるキャラクターを描画
        for chara in self.charas:
            chara.draw(screen, offset)
    def is_movable(self, x, y):
        """(x,y)は移動可能か？"""
        # マップ範囲内か？
        if x < 0 or x > self.col-1 or y < 0 or y > self.row-1:
            return False
        # マップチップは移動可能か？
        if self.map[y][x] == 1:  # 水は移動できない
            return False
       # キャラクターと衝突しないか？
        for chara in self.charas:
            if chara.x == x and chara.y == y:
                return False
        return True

class Character:
    """一般キャラクタークラス"""
    speed = 4  # 1フレームの移動ピクセル数
    animcycle = 24  # アニメーション速度
    frame = 0
    # キャラクターイメージ（mainで初期化）
    # キャラクター名 -> 分割画像リストの辞書
    images = {}
    def __init__(self, name, pos, dir, movetype):
        self.name = name  # プレイヤー名（ファイル名と同じ）
        self.image = self.images[name][0]  # 描画中のイメージ
        self.x, self.y = pos[0], pos[1]  # 座標（単位：マス）
        self.rect = self.image.get_rect(topleft=(self.x*GS, self.y*GS))
        self.vx, self.vy = 0, 0  # 移動速度
        self.moving = False  # 移動中か？
        self.direction = dir  # 向き
        self.movetype = movetype  # 移動タイプ
    def update(self, map):
        """キャラクター状態を更新する。
        mapは移動可能かの判定に必要。"""
        # プレイヤーの移動処理
        if self.moving == True:
            # ピクセル移動中ならマスにきっちり収まるまで移動を続ける
            self.rect.move_ip(self.vx, self.vy)
            # マスにおさまったら移動完了
            if self.rect.left % GS == 0 and self.rect.top % GS == 0:
                self.moving = False
                self.x = self.rect.left // GS
                self.y = self.rect.top // GS
        elif self.movetype == MOVE and random.random() < PROB_MOVE:
            # 移動中でないならPROB_MOVEの確率でランダム移動開始
            self.direction = random.randint(0, 3)  # 0-3のいずれか
            if self.direction == DOWN:
                if map.is_movable(self.x, self.y+1):
                    self.vx, self.vy = 0, self.speed
                    self.moving = True
            elif self.direction == LEFT:
                if map.is_movable(self.x-1, self.y):
                    self.vx, self.vy = -self.speed, 0
                    self.moving = True
            elif self.direction == RIGHT:
                if map.is_movable(self.x+1, self.y):
                    self.vx, self.vy = self.speed, 0
                    self.moving = True
            elif self.direction == UP:
                if map.is_movable(self.x, self.y-1):
                    self.vx, self.vy = 0, -self.speed
                    self.moving = True
        # キャラクターアニメーション
        self.frame += 1
        self.image = self.images[self.name][self.direction*4+self.frame//self.animcycle%4]
    def draw(self, screen, offset):
        """オフセットを考慮してプレイヤーを描画"""
        offsetx, offsety = offset
        px = self.rect.topleft[0]
        py = self.rect.topleft[1]
        screen.blit(self.image, (px-offsetx, py-offsety))

class Player(Character):
    def __init__(self, name, pos, dir):
        Character.__init__(self, name, pos, dir, False)
    def update(self, map):
        """プレイヤー状態を更新する。
        mapは移動可能かの判定に必要。"""
        # プレイヤーの移動処理
        if self.moving == True:
            # ピクセル移動中ならマスにきっちり収まるまで移動を続ける
            self.rect.move_ip(self.vx, self.vy)
            if self.rect.left % GS == 0 and self.rect.top % GS == 0:  # マスにおさまったら移動完了
                self.moving = False
                self.x = self.rect.left // GS
                self.y = self.rect.top // GS
                # TODO: ここに接触イベントのチェックを入れる
        else:
            # プレイヤーの場合、キー入力があったら移動を開始する
            pressed_keys = pygame.key.get_pressed()
            if pressed_keys[K_DOWN]:
                self.direction = DOWN  # 移動できるかに関係なく向きは変える
                if map.is_movable(self.x, self.y+1):
                    self.vx, self.vy = 0, self.speed
                    self.moving = True
            elif pressed_keys[K_LEFT]:
                self.direction = LEFT
                if map.is_movable(self.x-1, self.y):
                    self.vx, self.vy = -self.speed, 0
                    self.moving = True
            elif pressed_keys[K_RIGHT]:
                self.direction = RIGHT
                if map.is_movable(self.x+1, self.y):
                    self.vx, self.vy = self.speed, 0
                    self.moving = True
            elif pressed_keys[K_UP]:
                self.direction = UP
                if map.is_movable(self.x, self.y-1):
                    self.vx, self.vy = 0, -self.speed
                    self.moving = True
        # キャラクターアニメーション（frameに応じて描画イメージを切り替える）
        self.frame += 1
        self.image = self.images[self.name][self.direction*4+self.frame//self.animcycle%4]

if __name__ == "__main__":
    main()
