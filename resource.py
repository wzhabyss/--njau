# resource.py
import os
import sys
import pygame


class ResourceManager:
    def __init__(self):
        # 获取资源基础路径
        self.base_path = self.get_base_path()

        # 资源目录结构
        self.resource_dirs = {
            'images': os.path.join(self.base_path, 'images'),
            'sounds': os.path.join(self.base_path, 'sounds'),
            'fonts': os.path.join(self.base_path, 'fonts'),
            'data': os.path.join(self.base_path, 'data')
        }

        # 创建资源目录
        self.create_resource_dirs()

        # 资源缓存
        self.images = {}
        self.sounds = {}
        self.fonts = {}
        self.music = None

    def get_base_path(self):
        """获取资源基础路径，支持打包环境"""
        if getattr(sys, 'frozen', False):
            # 打包后的环境
            if hasattr(sys, '_MEIPASS'):
                return sys._MEIPASS
            else:
                return os.path.dirname(sys.executable)
        else:
            # 开发环境
            return os.path.dirname(os.path.abspath(__file__))

    def create_resource_dirs(self):
        """创建资源目录"""
        for dir_name, dir_path in self.resource_dirs.items():
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

    def get_resource_path(self, relative_path):
        """获取资源文件的完整路径"""
        # 首先尝试从资源目录查找
        for dir_name, dir_path in self.resource_dirs.items():
            full_path = os.path.join(dir_path, relative_path)
            if os.path.exists(full_path):
                return full_path

        # 如果找不到，返回相对于基础路径的路径
        return os.path.join(self.base_path, relative_path)

    def load_image(self, filename, scale=None, alpha=True):
        """加载图片资源"""
        cache_key = f"{filename}_{scale}"

        if cache_key in self.images:
            return self.images[cache_key]

        try:
            filepath = self.get_resource_path(os.path.join('images', filename))

            if not os.path.exists(filepath):
                print(f"⚠️  图片文件不存在: {filepath}")
                # 创建一个替代的彩色表面
                surface = pygame.Surface((50, 50))
                surface.fill((255, 0, 255))  # 洋红色作为缺失标记
                self.images[cache_key] = surface
                return surface

            if alpha:
                image = pygame.image.load(filepath).convert_alpha()
            else:
                image = pygame.image.load(filepath).convert()

            if scale:
                if isinstance(scale, (int, float)):
                    # 等比例缩放
                    width = int(image.get_width() * scale)
                    height = int(image.get_height() * scale)
                    image = pygame.transform.scale(image, (width, height))
                elif isinstance(scale, tuple) and len(scale) == 2:
                    # 指定宽高缩放
                    image = pygame.transform.scale(image, scale)

            self.images[cache_key] = image
            return image

        except Exception as e:
            print(f"❌ 加载图片失败 {filename}: {e}")
            # 返回一个替代的表面
            surface = pygame.Surface((50, 50))
            surface.fill((255, 0, 255))
            self.images[cache_key] = surface
            return surface

    def load_sound(self, filename, volume=0.5):
        """加载音效资源"""
        if filename in self.sounds:
            return self.sounds[filename]

        try:
            filepath = self.get_resource_path(os.path.join('sounds', filename))

            if not os.path.exists(filepath):
                print(f"⚠️  音效文件不存在: {filepath}")
                return None

            sound = pygame.mixer.Sound(filepath)
            sound.set_volume(volume)
            self.sounds[filename] = sound
            return sound

        except Exception as e:
            print(f"❌ 加载音效失败 {filename}: {e}")
            return None

    def load_music(self, filename, volume=0.3):
        """加载背景音乐"""
        try:
            filepath = self.get_resource_path(os.path.join('sounds', filename))

            if not os.path.exists(filepath):
                print(f"⚠️  音乐文件不存在: {filepath}")
                return False

            pygame.mixer.music.load(filepath)
            pygame.mixer.music.set_volume(volume)
            self.music = filename
            return True

        except Exception as e:
            print(f"❌ 加载音乐失败 {filename}: {e}")
            return False

    def load_font(self, filename, size=24, system_fallback=True):
        """加载字体"""
        cache_key = f"{filename}_{size}"

        if cache_key in self.fonts:
            return self.fonts[cache_key]

        try:
            # 首先尝试从fonts目录加载
            filepath = self.get_resource_path(os.path.join('fonts', filename))

            if os.path.exists(filepath):
                font = pygame.font.Font(filepath, size)
                self.fonts[cache_key] = font
                return font
            elif system_fallback:
                # 尝试系统字体
                font_names = [
                    'msyh.ttc',  # 微软雅黑
                    'simhei.ttf',  # 黑体
                    'simsun.ttc',  # 宋体
                    'arial.ttf',  # Arial
                    None  # Pygame默认字体
                ]

                for font_name in font_names:
                    try:
                        font = pygame.font.Font(font_name, size)
                        self.fonts[cache_key] = font
                        return font
                    except:
                        continue
        except Exception as e:
            print(f"❌ 加载字体失败: {e}")

        # 最后返回默认字体
        font = pygame.font.Font(None, size)
        self.fonts[cache_key] = font
        return font

    def play_music(self, filename=None, loops=-1, start=0.0, fade_ms=0):
        """播放背景音乐"""
        if filename and filename != self.music:
            if self.load_music(filename):
                pygame.mixer.music.play(loops, start, fade_ms)
                return True
            return False
        elif self.music:
            pygame.mixer.music.play(loops, start, fade_ms)
            return True
        return False

    def stop_music(self, fade_ms=0):
        """停止背景音乐"""
        if fade_ms > 0:
            pygame.mixer.music.fadeout(fade_ms)
        else:
            pygame.mixer.music.stop()

    def pause_music(self):
        """暂停背景音乐"""
        pygame.mixer.music.pause()

    def unpause_music(self):
        """继续播放背景音乐"""
        pygame.mixer.music.unpause()

    def clear_cache(self):
        """清除资源缓存"""
        self.images.clear()
        self.sounds.clear()
        self.fonts.clear()

    def get_file_size(self, filename):
        """获取文件大小"""
        filepath = self.get_resource_path(filename)
        if os.path.exists(filepath):
            return os.path.getsize(filepath)
        return 0

    def list_resources(self, directory):
        """列出目录中的资源文件"""
        dir_path = self.get_resource_path(directory)
        if os.path.exists(dir_path):
            return os.listdir(dir_path)
        return []