# game_resources.py
import os

import pygame
from resource import ResourceManager


class GameResources:
    def __init__(self):
        self.resource_manager = ResourceManager()
        self.fonts = {}
        self.images = {}
        self.sounds = {}
        self.load_all()

    def load_all(self):
        """加载所有游戏资源"""
        self.load_fonts()
        self.load_images()
        self.load_sounds()

    def load_fonts(self):
        """加载字体"""
        # 使用你的字体逻辑
        font_dir = "C:/Windows/Fonts/"
        font_paths = [
            "msyh.ttc",
            "msyhbd.ttc",
            "simhei.ttf",
            "simsun.ttc",
        ]

        font_path = None
        for f in font_paths:
            p = os.path.join(font_dir, f)
            if os.path.exists(p):
                font_path = p
                break

        if font_path:
            self.fonts = {
                "large": pygame.font.Font(font_path, 48),
                "medium": pygame.font.Font(font_path, 32),
                "normal": pygame.font.Font(font_path, 24),
                "small": pygame.font.Font(font_path, 18),
            }
        else:
            self.fonts = {
                "large": pygame.font.Font(None, 48),
                "medium": pygame.font.Font(None, 32),
                "normal": pygame.font.Font(None, 24),
                "small": pygame.font.Font(None, 18),
            }

    def load_images(self):
        """加载图像资源"""
        # 首先尝试使用资源管理器加载图像
        try:
            player_img = self.resource_manager.load_image('player.png', create_if_missing=self.create_player_image)
            enemy_img = self.resource_manager.load_image('enemy.png', create_if_missing=self.create_enemy_image)
            bullet_img = self.resource_manager.load_image('bullet.png', create_if_missing=self.create_bullet_image)
            health_img = self.resource_manager.load_image('health_pack.png',
                                                          create_if_missing=self.create_health_pack_image)
            bullet_pack_img = self.resource_manager.load_image('bullet_pack.png',
                                                               create_if_missing=self.create_bullet_pack_image)

            if player_img:
                self.images['player'] = player_img
            if enemy_img:
                self.images['enemy'] = enemy_img
            if bullet_img:
                self.images['bullet'] = bullet_img
            if health_img:
                self.images['health_pack'] = health_img
            if bullet_pack_img:
                self.images['bullet_pack'] = bullet_pack_img
        except:
            # 如果加载失败，创建默认图像
            print("使用默认图像资源")
            self.create_default_images()

    def create_default_images(self):
        """创建默认图像"""
        self.images['player'] = self.create_player_image()
        self.images['enemy'] = self.create_enemy_image()
        self.images['bullet'] = self.create_bullet_image()
        self.images['health_pack'] = self.create_health_pack_image()
        self.images['bullet_pack'] = self.create_bullet_pack_image()

        # 添加特殊敌机图像
        self.images['elite_enemy'] = self.create_elite_enemy_image()
        self.images['tracking_enemy'] = self.create_tracking_enemy_image()

    def load_sounds(self):
        """加载音效资源"""
        try:
            # 尝试使用资源管理器加载音效
            shoot_sound = self.resource_manager.load_sound('shoot.wav', 0.1)
            explosion_sound = self.resource_manager.load_sound('explosion.wav', 0.2)
            hit_sound = self.resource_manager.load_sound('hit.wav', 0.4)
            powerup_sound = self.resource_manager.load_sound('powerup.wav', 0.3)
            click_sound = self.resource_manager.load_sound('click.wav', 0.4)
            game_over_sound = self.resource_manager.load_sound('gameover.wav',0.5)
            warn_sound = self.resource_manager.load_sound('warn.wav',0.8)
            flash_sound = self.resource_manager.load_sound('flash.wav',0.6)
            flash_back = self.resource_manager.load_sound('flashback.wav',0.2)
            time_freeze = self.resource_manager.load_sound('timefreeze.wav',1.5)



            if shoot_sound:
                self.sounds['shoot'] = shoot_sound
            if explosion_sound:
                self.sounds['explosion'] = explosion_sound
            if hit_sound:
                self.sounds['hit'] = hit_sound
            if powerup_sound:
                self.sounds['powerup'] = powerup_sound
            if click_sound:
                self.sounds['click'] = click_sound
            if game_over_sound:
                self.sounds['game_over'] = game_over_sound
            if warn_sound:
                self.sounds['warn'] = warn_sound
            if flash_sound:
                self.sounds['flash'] = flash_sound
            if flash_back:
                self.sounds['flashback'] = flash_back
            if time_freeze:
                self.sounds['timefreeze'] = time_freeze

        except:
            # 如果音效加载失败，使用空的音效
            print("音效加载失败，使用静音模式")
            self.sounds = {
                'shoot': None,
                'explosion': None,
                'hit': None,
                'powerup': None,
                'click': None,
                'gameover': None
            }

    def create_player_image(self):
        """创建玩家飞机图像"""
        surf = pygame.Surface((50, 40), pygame.SRCALPHA)
        # 蓝色三角形飞机
        points = [(25, 0), (0, 40), (50, 40)]
        pygame.draw.polygon(surf, (0, 120, 255), points)
        pygame.draw.rect(surf, (0, 120, 255), (15, 20, 20, 10))
        return surf

    def create_enemy_image(self):
        """创建敌机图像"""
        surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        points = [(20, 40), (0, 0), (40, 0)]
        pygame.draw.polygon(surf, (255, 50, 50), points)
        pygame.draw.rect(surf, (255, 50, 50), (10, 15, 20, 8))
        return surf

    def create_elite_enemy_image(self):
        """创建精英敌机图像"""
        surf = pygame.Surface((60, 50), pygame.SRCALPHA)
        # 紫色菱形
        points = [(30, 0), (60, 25), (30, 50), (0, 25)]
        pygame.draw.polygon(surf, (180, 0, 255), points)
        # 添加细节
        pygame.draw.polygon(surf, (200, 50, 255), points, 2)
        return surf

    def create_tracking_enemy_image(self):
        """创建追踪敌机图像"""
        surf = pygame.Surface((45, 45), pygame.SRCALPHA)
        # 青色八边形
        points = []
        center_x, center_y = 22.5, 22.5
        radius = 20
        for i in range(8):
            angle = 3.14159 * i / 4
            x = center_x + radius * pygame.math.Vector2(1, 0).rotate_rad(angle).x
            y = center_y + radius * pygame.math.Vector2(1, 0).rotate_rad(angle).y
            points.append((x, y))
        pygame.draw.polygon(surf, (0, 255, 255), points)
        return surf

    def create_bullet_image(self):
        """创建子弹图像"""
        surf = pygame.Surface((5, 15), pygame.SRCALPHA)
        pygame.draw.rect(surf, (255, 255, 0), (0, 0, 5, 15))
        pygame.draw.rect(surf, (255, 200, 0), (1, 1, 3, 13))
        return surf

    def create_health_pack_image(self):
        """创建血包图像"""
        surf = pygame.Surface((30, 30), pygame.SRCALPHA)
        # 绿色十字
        pygame.draw.rect(surf, (0, 255, 0), (10, 0, 10, 30))
        pygame.draw.rect(surf, (0, 255, 0), (0, 10, 30, 10))
        # 白色边框
        pygame.draw.rect(surf, (255, 255, 255), (0, 0, 30, 30), 2)
        return surf

    def create_bullet_pack_image(self):
        """创建子弹包图像"""
        surf = pygame.Surface((30, 30), pygame.SRCALPHA)
        # 粉色三角形
        points = [(15, 5), (5, 25), (25, 25)]
        pygame.draw.polygon(surf, (255, 105, 180), points)
        # 加号
        pygame.draw.rect(surf, (255, 255, 255), (10, 13, 10, 4))
        pygame.draw.rect(surf, (255, 255, 255), (13, 10, 4, 10))
        pygame.draw.rect(surf, (255, 255, 255), (0, 0, 30, 30), 2)
        return surf

    def play_sound(self, sound_name):
        """播放音效"""
        if sound_name in self.sounds and self.sounds[sound_name]:
            self.sounds[sound_name].play()