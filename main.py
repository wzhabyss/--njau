import hashlib
import math
import os
import random
import sys
import mysql.connector
import pygame
from mysql.connector import Error
# 在main.py的import部分添加
from resource import ResourceManager
from game_resources import GameResources
# 创建资源管理器
resource_manager = ResourceManager()
# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入资源路径工具
try:
    from utils import resource_path, file_exists
except ImportError:
    # 如果utils.py不存在，创建简单的版本
    def resource_path(relative_path):
        """简单的资源路径函数"""
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)


    def file_exists(file_path):
        return os.path.exists(resource_path(file_path))


    # 原来的导入方式
    # import config
    # import user

    # 新的导入方式，确保能找到模块
    try:
        import config
        import user
    except ImportError:
        # 如果直接导入失败，尝试从当前目录导入
        import importlib.util

        # 动态导入config.py
        config_spec = importlib.util.spec_from_file_location(
            "config",
            resource_path("config.py")
        )
        config = importlib.util.module_from_spec(config_spec)
        config_spec.loader.exec_module(config)

        # 动态导入user.py
        user_spec = importlib.util.spec_from_file_location(
            "user",
            resource_path("user.py")
        )
        user = importlib.util.module_from_spec(user_spec)
        user_spec.loader.exec_module(user)
# 初始化 Pygame
pygame.init()

# 游戏窗口设置
WIDTH, HEIGHT = 1200, 1000
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("我爱打飞机")

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 120, 255)
YELLOW = (255, 255, 0)
PURPLE = (180, 0, 255)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)  # 青色，用于追踪敌机
PINK = (255, 105, 180)  # 粉色，用于子弹包
LIGHT_BLUE = (100, 149, 237)  # 登录界面颜色
DARK_BLUE = (25, 25, 112)  # 暗蓝色


def init_global_fonts(resource_manager=None):
    """初始化全局字体，支持资源管理器"""



    # 原来的字体加载逻辑（保持兼容性）
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
        return {
            "large": pygame.font.Font(font_path, 48),
            "medium": pygame.font.Font(font_path, 32),
            "normal": pygame.font.Font(font_path, 24),
            "small": pygame.font.Font(font_path, 18),
        }
    else:
        return {
            "large": pygame.font.Font(None, 48),
            "medium": pygame.font.Font(None, 32),
            "normal": pygame.font.Font(None, 24),
            "small": pygame.font.Font(None, 18),
        }

FONTS = init_global_fonts()


# 用户管理类
class UserManager:
    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = "wzh040916"
        self.database = "plane_game_db"
        self.current_user = None
        self.connection = None
        self.cursor = None
        self.local_mode = True  # 默认为本地模式
        self.local_users = {}  # 本地用户存储

        # 尝试连接MySQL，如果失败则使用本地模式
        try:
            if self.connect():
                print("✅ MySQL数据库连接成功")
                self.local_mode = False
            else:
                print("⚠️  MySQL连接失败，使用本地模式")
                self.init_local_storage()
        except Exception as e:
            print(f"⚠️  数据库错误: {e}，使用本地模式")
            self.init_local_storage()

    def init_local_storage(self):
        """初始化本地存储"""
        self.local_mode = True
        self.local_users = {}  # 本地用户存储
        print("✅ 本地存储模式已初始化")

    def connect(self):
        """连接到MySQL数据库"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor = self.connection.cursor()
            print("数据库连接成功")
            return True
        except Error as e:
            print(f"数据库连接失败: {e}")
            return False

    def hash_password(self, password):
        """对密码进行哈希处理"""
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, username, password, email=''):
        """注册新用户"""
        if self.local_mode:
            # 本地模式注册
            return self.register_local(username, password, email)

        # MySQL模式注册
        try:
            # 确保有cursor
            if not self.cursor:
                if not self.connect():
                    return False, "数据库连接失败"

            # 检查用户名是否已存在
            self.cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if self.cursor.fetchone():
                return False, "用户名已存在"

            # 插入新用户
            password_hash = self.hash_password(password)
            self.cursor.execute(
                "INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)",
                (username, password_hash, email)
            )

            user_id = self.cursor.lastrowid

            # 初始化用户统计
            self.cursor.execute(
                "INSERT INTO user_stats (user_id) VALUES (%s)",
                (user_id,)
            )

            self.connection.commit()
            return True, "注册成功"
        except Exception as e:
            return False, f"注册失败: {str(e)}"

    def register_local(self, username, password, email=''):
        """本地模式注册"""
        # 检查用户名是否已存在
        if username in self.local_users:
            return False, "用户名已存在"

        # 创建本地用户
        user_id = len(self.local_users) + 1
        password_hash = self.hash_password(password)

        self.local_users[username] = {
            'id': user_id,
            'username': username,
            'password_hash': password_hash,
            'email': email
        }

        return True, "注册成功（本地模式）"

    def login(self, username, password):
        """用户登录"""
        if self.local_mode:
            # 本地模式登录
            return self.login_local(username, password)

        # MySQL模式登录
        password_hash = self.hash_password(password)

        try:
            if not self.cursor:
                if not self.connect():
                    return False, "数据库连接失败"

            self.cursor.execute(
                "SELECT id, username FROM users WHERE username = %s AND password_hash = %s",
                (username, password_hash)
            )

            user = self.cursor.fetchone()
            if user:
                self.current_user = {'id': user[0], 'username': user[1]}

                # 更新最后登录时间
                self.cursor.execute(
                    "UPDATE users SET last_login = NOW() WHERE id = %s",
                    (user[0],)
                )
                self.connection.commit()

                return True, "登录成功"
            return False, "用户名或密码错误"
        except Exception as e:
            return False, f"登录失败: {str(e)}"

    def login_local(self, username, password):
        """本地模式登录"""
        password_hash = self.hash_password(password)

        if username in self.local_users:
            user = self.local_users[username]
            if user['password_hash'] == password_hash:
                self.current_user = {'id': user['id'], 'username': username}
                return True, "登录成功（本地模式）"

        return False, "用户名或密码错误"

    def logout(self):
        """用户登出"""
        self.current_user = None

    def save_score(self, score, difficulty, game_time, bullet_damage, enemies_killed=0):
        """保存游戏分数"""
        if self.local_mode:
            # 本地模式保存
            return self.save_score_local(score, difficulty, game_time, bullet_damage, enemies_killed)

        if not self.current_user:
            return False

        try:
            user_id = self.current_user['id']

            # 确保有cursor
            if not self.cursor:
                if not self.connect():
                    return False

            # 保存游戏记录
            self.cursor.execute("""
                INSERT INTO game_records 
                (user_id, score, difficulty_level, game_time, bullet_damage, enemies_killed)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, score, difficulty, game_time, bullet_damage, enemies_killed))

            # 更新用户统计
            self.cursor.execute("""
                UPDATE user_stats 
                SET total_games = total_games + 1,
                    total_score = total_score + %s,
                    total_game_time = total_game_time + %s,
                    last_played = NOW()
                WHERE user_id = %s
            """, (score, game_time, user_id))

            # 更新最高分
            self.cursor.execute("""
                UPDATE user_stats 
                SET highest_score = GREATEST(highest_score, %s)
                WHERE user_id = %s
            """, (score, user_id))

            # 更新最高难度
            self.cursor.execute("""
                UPDATE user_stats 
                SET highest_difficulty = GREATEST(highest_difficulty, %s)
                WHERE user_id = %s
            """, (difficulty, user_id))

            self.connection.commit()
            return True
        except Exception as e:
            print(f"保存分数失败: {e}")
            return False

    def save_score_local(self, score, difficulty, game_time, bullet_damage, enemies_killed=0):
        """本地模式保存分数"""
        try:
            import json
            import datetime
            import os

            score_data = {
                'username': self.current_user['username'] if self.current_user else '游客',
                'score': score,
                'difficulty': difficulty,
                'game_time': game_time,
                'bullet_damage': bullet_damage,
                'enemies_killed': enemies_killed,
                'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # 保存到文件
            filename = 'game_scores.json'
            scores = []

            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    try:
                        scores = json.load(f)
                    except:
                        scores = []

            scores.append(score_data)

            # 只保留最近100条记录
            if len(scores) > 100:
                scores = scores[-100:]

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(scores, f, ensure_ascii=False, indent=2)

            print(f"✅ 分数已保存到本地文件: {score}")
            return True
        except Exception as e:
            print(f"❌ 本地保存失败: {e}")
            return False

    def get_leaderboard(self, limit=10):
        """获取排行榜"""
        if self.local_mode:
            # 本地模式排行榜
            return self.get_leaderboard_local(limit)

        try:
            # 确保有cursor
            if not self.cursor:
                if not self.connect():
                    return []

            self.cursor.execute("""
                SELECT u.username, g.score, g.difficulty_level, 
                       g.game_time, g.date_played
                FROM game_records g
                JOIN users u ON g.user_id = u.id
                ORDER BY g.score DESC
                LIMIT %s
            """, (limit,))

            return self.cursor.fetchall()
        except Exception as e:
            print(f"获取排行榜失败: {e}")
            return []

    def get_leaderboard_local(self, limit=10):
        """本地模式获取排行榜"""
        try:
            import json
            import os

            filename = 'game_scores.json'
            if not os.path.exists(filename):
                return []

            with open(filename, 'r', encoding='utf-8') as f:
                scores = json.load(f)

            # 按分数排序
            scores.sort(key=lambda x: x['score'], reverse=True)

            # 转换为与MySQL相同的格式
            leaderboard = []
            for score_data in scores[:limit]:
                leaderboard.append((
                    score_data.get('username', '本地玩家'),
                    score_data['score'],
                    score_data['difficulty'],
                    score_data['game_time'],
                    score_data['date']
                ))

            return leaderboard
        except Exception as e:
            print(f"获取本地排行榜失败: {e}")
            return []

    def get_user_stats(self):
        """获取当前用户统计"""
        if self.local_mode:
            # 本地模式用户统计
            return self.get_user_stats_local()

        if not self.current_user:
            return None

        try:
            user_id = self.current_user['id']

            # 确保有cursor
            if not self.cursor:
                if not self.connect():
                    return None

            self.cursor.execute("""
                SELECT total_games, total_score, highest_score, 
                       total_game_time, highest_difficulty, last_played
                FROM user_stats 
                WHERE user_id = %s
            """, (user_id,))

            stats = self.cursor.fetchone()
            if stats:
                return {
                    'username': self.current_user['username'],
                    'total_games': stats[0],
                    'total_score': stats[1],
                    'highest_score': stats[2],
                    'total_game_time': stats[3],
                    'highest_difficulty': stats[4],
                    'last_played': stats[5]
                }
            return None
        except Exception as e:
            print(f"获取用户统计失败: {e}")
            return None

    def get_user_stats_local(self):
        """本地模式获取用户统计"""
        if not self.current_user:
            return None

        try:
            import json
            import os

            filename = 'game_scores.json'
            if not os.path.exists(filename):
                return {
                    'username': self.current_user['username'],
                    'total_games': 0,
                    'total_score': 0,
                    'highest_score': 0,
                    'total_game_time': 0,
                    'highest_difficulty': 0,
                    'last_played': None
                }

            with open(filename, 'r', encoding='utf-8') as f:
                scores = json.load(f)

            # 筛选当前用户的分数
            user_scores = [s for s in scores if s.get('username') == self.current_user['username']]

            if not user_scores:
                return {
                    'username': self.current_user['username'],
                    'total_games': 0,
                    'total_score': 0,
                    'highest_score': 0,
                    'total_game_time': 0,
                    'highest_difficulty': 0,
                    'last_played': None
                }

            total_games = len(user_scores)
            total_score = sum(s['score'] for s in user_scores)
            highest_score = max(s['score'] for s in user_scores)
            total_game_time = sum(s['game_time'] for s in user_scores)
            highest_difficulty = max(s['difficulty'] for s in user_scores)
            last_played = user_scores[-1]['date'] if user_scores else None

            return {
                'username': self.current_user['username'],
                'total_games': total_games,
                'total_score': total_score,
                'highest_score': highest_score,
                'total_game_time': total_game_time,
                'highest_difficulty': highest_difficulty,
                'last_played': last_played
            }
        except Exception as e:
            print(f"获取本地用户统计失败: {e}")
            return None

    def close(self):
        """关闭数据库连接"""
        if not self.local_mode and self.connection and hasattr(self.connection,
                                                               'is_connected') and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("数据库连接已关闭")

# 玩家飞机类
class Player:
    def __init__(self, game_resources):
        self.game_resources = game_resources
        self.width = 50
        self.height = 40
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT - self.height - 20
        self.speed = 6
        self.color = BLUE
        self.health = 3
        self.max_health = 15
        self.score = 0
        self.bullets = []
        self.shoot_cooldown = 0
        self.shoot_interval = 10  # 射击间隔（10帧 = 约0.17秒）← 保持不变
        self.invincible = 0
        self.bullet_damage = 1
        self.enemies_killed = 0
        self.level = 1

        # ========== 添加Boss击杀记录 ==========
        self.boss_killed = 0
        # =====================================
        # 添加自动射击标志
        self.auto_fire = True  # 默认开启自动射击 ← 新增

        self.skill_cooldown = 0  # 技能当前冷却时间（帧数）
        self.skill_max_cooldown = 15 * 60  # 技能最大冷却时间：30秒 * 60帧/秒 = 1800帧
        self.skill_ready = False  # 技能是否准备好
        self.skill_charge = 0  # 技能充能进度（0-100%）
        self.skill_active = False  # 技能是否正在使用
        self.skill_use_time = 0  # 技能使用时间（用于特效等）
        self.skill_effect_duration = 20  # 技能特效持续时间（帧数）

        # ========== 新增春秋蝉技能属性 ==========
        self.skill2_cooldown = 0  # 春秋蝉技能当前冷却时间（帧数）
        self.skill2_max_cooldown = 30 * 60  # 春秋蝉技能最大冷却时间：60秒 * 60帧/秒 = 3600帧
        self.skill2_ready = False  # 春秋蝉技能是否准备好
        self.skill2_charge = 0  # 春秋蝉技能充能进度（0-100%）
        self.skill2_active = False  # 春秋蝉技能是否正在使用
        self.skill2_use_time = 0  # 春秋蝉技能使用时间（用于特效等）
        self.skill2_effect_duration = 60  # 春秋蝉技能特效持续时间（帧数）

        # 位置记录（用于时光回溯）
        self.position_history = []  # 存储最近的位置记录
        self.max_history_length = 120  # 最多记录120帧（2秒）的位置

        # 春秋蝉特效相关
        self.skill2_afterimages = []  # 残影列表
        self.skill2_time_warp_effect = False  # 时间扭曲特效
        # ========== 春秋蝉技能虚影相关属性 ==========
        self.rewind_ghost = None  # 要闪回的虚影位置
        self.ghost_alpha = -200  # 虚影透明度（-200-255）
        self.ghost_visible = False  # 虚影是否可见
        self.ghost_blink_timer = 0  # 虚影闪烁计时器
        self.ghost_update_timer = 0  # 虚影更新计时器
        self.ghost_update_interval = 1  # 每1帧更新一次虚影（0.5秒）
        # ==========================================
        # ========== 时停领域技能属性 ==========
        self.time_field_cooldown = 0  # 当前冷却时间（帧数）
        self.time_field_max_cooldown = 50 * 60  # 最大冷却时间：45秒 * 60帧/秒 = 2700帧
        self.time_field_ready = False  # 技能是否准备好
        self.time_field_charge = 0  # 技能充能进度（0-100%）
        self.time_field_active = False  # 技能是否激活
        self.time_field_duration = 9 * 60  # 持续时间：3秒 * 60帧 = 180帧
        self.time_field_use_time = 0  # 技能已使用时间
        self.time_field_center = None  # 领域中心位置
        self.time_field_radius = 300  # 领域半径
        self.time_field_bullet_slow = 0.3  # 子弹速度降低70%（保留30%速度）
        self.time_field_player_speed = 1.5  # 玩家速度提升50%
        self.time_field_particles = []  # 领域特效粒子
        self._time_field_affected_enemies = []  # 记录所有受时停影响的敌人
        # =====================================
        # ====================================

        # 使用游戏资源中的图像
        if hasattr(game_resources, 'images') and 'player' in game_resources.images:
            self.image = game_resources.images['player']
        else:
            self.image = None

    def update_skill(self):
        """更新技能状态"""
        # 更新技能冷却
        if self.skill_cooldown > 0:
            self.skill_cooldown -= 1

            # 计算充能进度
            self.skill_charge = 100 - (self.skill_cooldown / self.skill_max_cooldown * 100)
            self.skill_ready = False
        else:
            self.skill_cooldown = 0
            self.skill_charge = 100
            self.skill_ready = True

        # 更新技能特效
        if self.skill_active:
            self.skill_use_time += 1
            if self.skill_use_time >= self.skill_effect_duration:
                self.skill_active = False
                self.skill_use_time = 0

    def use_skill1(self, target_x, target_y):
        """使用技能：瞬移到目标位置"""
        if self.skill_ready and not self.skill_active:
            # 保存当前位置（用于特效）
            self.old_x, self.old_y = self.x, self.y

            # 瞬移到目标位置（考虑玩家中心点）
            self.x = target_x - self.width // 2
            self.y = target_y - self.height // 2

            # 边界检查
            self.x = max(0, min(self.x, WIDTH - self.width))
            self.y = max(0, min(self.y, HEIGHT - self.height))

            # 启动冷却
            self.skill_cooldown = self.skill_max_cooldown
            self.skill_ready = False
            self.skill_active = True
            self.skill_use_time = 0



            # 播放音效
            self.game_resources.play_sound('flash')

            print(f"✨ 技能使用！瞬移到 ({target_x}, {target_y})")
            return True
        return False

    def update_skill2(self):
        """更新春秋蝉技能状态"""
        if self.skill2_cooldown > 0:
            self.skill2_cooldown -= 1
            self.skill2_charge = 100 - (self.skill2_cooldown / self.skill2_max_cooldown * 100)
            self.skill2_ready = False
        else:
            self.skill2_cooldown = 0
            self.skill2_charge = 100
            self.skill2_ready = True

        # 更新技能特效
        if self.skill2_active:
            self.skill2_use_time += 1

            # 更新残影
            for afterimage in self.skill2_afterimages[:]:
                afterimage['alpha'] -= 10  # 逐渐淡出
                afterimage['frame'] += 1
                if afterimage['alpha'] <= 0:
                    self.skill2_afterimages.remove(afterimage)

            if self.skill2_use_time >= self.skill2_effect_duration:
                self.skill2_active = False
                self.skill2_use_time = 0
                self.skill2_time_warp_effect = False

    def use_skill2(self):
        """使用春秋蝉技能：回到2秒前的位置并获得2秒无敌"""
        if self.skill2_ready and not self.skill2_active and len(self.position_history) >= 60:  # 至少1秒历史
            # 初始化target_pos变量
            target_pos = None

            # 如果有虚影，使用虚影位置
            if self.ghost_visible and self.rewind_ghost:
                target_x = self.rewind_ghost['x']
                target_y = self.rewind_ghost['y']
                # 创建target_pos字典用于特效
                target_pos = {'x': target_x, 'y': target_y}
            else:
                # 获取2秒前的位置（120帧前）
                target_frame = len(self.position_history) - 120
                if target_frame >= 0:  # 确保索引有效
                    target_pos = self.position_history[target_frame]
                    target_x = target_pos['x']
                    target_y = target_pos['y']
                else:
                    # 如果历史记录不够120帧，使用最旧的位置
                    target_pos = self.position_history[0]
                    target_x = target_pos['x']
                    target_y = target_pos['y']

            # 检查target_pos是否成功获取
            if target_pos is None:
                print("⚠️ 春秋蝉技能：无法获取目标位置")
                return False

            # 保存当前位置（用于特效）
            self.skill2_old_pos = {'x': self.x, 'y': self.y}

            # 时光回溯：回到目标位置
            self.x = target_x
            self.y = target_y

            # 边界检查
            self.x = max(0, min(self.x, WIDTH - self.width))
            self.y = max(0, min(self.y, HEIGHT - self.height))

            # 获得2秒无敌（120帧）
            self.invincible = max(self.invincible, 120)

            # 创建时光回溯特效 - 现在target_pos已经被正确定义
            self.create_time_warp_effect(self.skill2_old_pos, target_pos)

            # 启动冷却
            self.skill2_cooldown = self.skill2_max_cooldown
            self.skill2_ready = False
            self.skill2_active = True
            self.skill2_use_time = 0
            self.skill2_time_warp_effect = True

            # 隐藏虚影
            self.ghost_visible = False
            self.rewind_ghost = None

            # 清空历史记录（避免循环回溯）
            # 注意：这里应该根据实际使用的帧数来清空
            used_frame = len(self.position_history) - 120 if len(self.position_history) >= 120 else 0
            self.position_history = self.position_history[:max(0, used_frame)]

            # 播放音效
            if hasattr(self.game_resources, 'play_sound'):
                self.game_resources.play_sound('flashback')

            print(f"🦋 春秋蝉技能使用！回到位置 ({target_x}, {target_y})")
            return True

        elif len(self.position_history) < 60:
            print("⚠️ 春秋蝉技能：历史记录不足，需要至少1秒的游戏时间")
            return False

        return False

    def create_time_warp_effect(self, old_pos, new_pos):
        """创建时光回溯特效"""
        # 清空残影列表
        self.skill2_afterimages = []

        # 创建多个残影
        for i in range(10):
            # 在旧位置和新位置之间插值
            t = i / 9.0
            x = old_pos['x'] * (1 - t) + new_pos['x'] * t
            y = old_pos['y'] * (1 - t) + new_pos['y'] * t

            self.skill2_afterimages.append({
                'x': x,
                'y': y,
                'alpha': 200 - i * 20,  # 逐渐变淡
                'frame': 0,
                'width': self.width,
                'height': self.height
            })

    def update_time_field(self):
        """更新时停领域状态"""
        # 更新技能冷却
        if self.time_field_cooldown > 0:
            self.time_field_cooldown -= 1
            self.time_field_charge = 100 - (self.time_field_cooldown / self.time_field_max_cooldown * 100)
            self.time_field_ready = False
        else:
            self.time_field_cooldown = 0
            self.time_field_charge = 100
            self.time_field_ready = True

        # 更新技能激活状态
        if self.time_field_active:
            self.time_field_use_time += 1

            # 更新领域特效粒子
            self.update_time_field_particles()

            # 检查技能是否结束
            if self.time_field_use_time >= self.time_field_duration:
                # 技能结束时清理所有时停效果
                self.deactivate_time_field()

                # 恢复正常速度
                self.speed = self.speed / self.time_field_player_speed

    def deactivate_time_field(self):
        """停用时停领域，恢复所有受影响的目标"""
        # 恢复受影响的敌人
        if hasattr(self, '_time_field_affected_enemies'):
            for enemy in self._time_field_affected_enemies:
                if hasattr(enemy, 'is_slowed') and enemy.is_slowed:
                    if hasattr(enemy, 'original_speed'):
                        enemy.speed = enemy.original_speed
                    enemy.is_slowed = False
                    enemy.slow_factor = 1.0

                    # 恢复子弹速度
                    if hasattr(enemy, 'bullets'):
                        for bullet in enemy.bullets:
                            if hasattr(bullet, 'original_speed'):
                                bullet.speed = bullet.original_speed

            # 清空列表
            self._time_field_affected_enemies.clear()

        # 重置技能状态
        self.time_field_active = False
        self.time_field_use_time = 0
        self.time_field_center = None
        self.time_field_particles = []

    def update_time_field_particles(self):
        """更新时停领域特效粒子"""
        if not self.time_field_active or not self.time_field_center:
            return

        # 添加新粒子
        if random.random() < 0.3:  # 30%概率添加新粒子
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, self.time_field_radius)

            self.time_field_particles.append({
                'x': self.time_field_center[0] + math.cos(angle) * distance,
                'y': self.time_field_center[1] + math.sin(angle) * distance,
                'size': random.uniform(1.5, 3.0),
                'alpha': random.randint(100, 180),
                'speed': random.uniform(0.1, 0.3),
                'angle': angle + random.uniform(-0.1, 0.1),
                'life': random.randint(30, 60),
                'max_life': random.randint(30, 60)
            })

        # 更新现有粒子
        for particle in self.time_field_particles[:]:
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.time_field_particles.remove(particle)
                continue

            # 粒子缓慢旋转
            particle['x'] += math.cos(particle['angle']) * particle['speed']
            particle['y'] += math.sin(particle['angle']) * particle['speed']
            particle['alpha'] = int(particle['alpha'] * (particle['life'] / particle['max_life']))

    def use_time_field(self):
        """使用时停领域技能"""
        if self.time_field_ready and not self.time_field_active:
            # 设置领域中心为玩家当前位置
            self.time_field_center = (self.x + self.width // 2, self.y + self.height // 2)

            # 激活技能
            self.time_field_active = True
            self.time_field_use_time = 0
            self.time_field_ready = False
            self.time_field_cooldown = self.time_field_max_cooldown

            # 清空受影响敌人列表（重新开始）
            if hasattr(self, '_time_field_affected_enemies'):
                self._time_field_affected_enemies.clear()

            # 提升玩家速度
            self.speed = self.speed * self.time_field_player_speed

            # 初始化粒子
            self.time_field_particles = []

            # 播放音效
            if hasattr(self.game_resources, 'play_sound'):
                self.game_resources.play_sound('timefreeze')

            print("🕒 时停领域激活！")
            return True
        return False

    def get_time_field_cooldown_seconds(self):
        """获取时停领域剩余冷却时间（秒）"""
        return self.time_field_cooldown // 60

    def is_in_time_field(self, x, y):
        """检查坐标是否在时停领域内"""
        if not self.time_field_active or not self.time_field_center:
            return False

        center_x, center_y = self.time_field_center
        distance = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
        return distance <= self.time_field_radius

    def reset_skill(self):
        """重置技能（用于游戏重新开始）"""
        self.skill_cooldown = 0
        self.skill_charge = 0
        self.skill_ready = False
        self.skill_active = False
        self.skill_use_time = 0

        # 重置春秋蝉技能
        self.skill2_cooldown = 0
        self.skill2_charge = 0
        self.skill2_ready = False
        self.skill2_active = False
        self.skill2_use_time = 0
        self.position_history = []
        self.skill2_afterimages = []
        self.skill2_time_warp_effect = False

        # 重置虚影
        self.rewind_ghost = None
        self.ghost_alpha = 0
        self.ghost_visible = False
        self.ghost_blink_timer = 0
        self.ghost_update_timer = 0

    def get_skill1_cooldown_seconds(self):
        """获取技能剩余冷却时间（秒）"""
        return self.skill_cooldown // 60

    def get_skill2_cooldown_seconds(self):
        """获取春秋蝉技能剩余冷却时间（秒）"""
        return self.skill2_cooldown // 60

    def draw(self):
        # ========== 绘制技能特效（优先绘制，作为背景效果） ==========

        # ========== 绘制春秋蝉技能虚影（新增） ==========
        # 在技能就绪且有足够历史记录时，显示要闪回位置的虚影
        if (hasattr(self, 'skill2_ready') and self.skill2_ready and
                hasattr(self, 'ghost_visible') and self.ghost_visible and
                hasattr(self, 'rewind_ghost') and self.rewind_ghost):

            ghost_x = self.rewind_ghost['x']
            ghost_y = self.rewind_ghost['y']
            ghost_width = self.rewind_ghost['width']
            ghost_height = self.rewind_ghost['height']
            ghost_alpha = self.rewind_ghost.get('alpha', 180)

            # 绘制半透明虚影主体
            if self.image:
                # 有图像的情况
                ghost_image = self.image.copy()
                ghost_image.set_alpha(ghost_alpha)
                screen.blit(ghost_image, (ghost_x, ghost_y))
            else:
                # 无图像的情况
                ghost_surface = pygame.Surface((ghost_width, ghost_height), pygame.SRCALPHA)
                pygame.draw.polygon(ghost_surface, (100, 255, 100, ghost_alpha), [
                    (ghost_width // 2, 0),
                    (0, ghost_height),
                    (ghost_width, ghost_height)
                ])
                screen.blit(ghost_surface, (ghost_x, ghost_y))

            # 绘制虚影轮廓（闪烁效果）
            if hasattr(self, 'ghost_blink_timer') and self.ghost_blink_timer % 20 < 10:
                # 绘制发光轮廓
                if self.image:
                    outline_rect = pygame.Rect(
                        ghost_x - 2,
                        ghost_y - 2,
                        ghost_width + 4,
                        ghost_height + 4
                    )
                    outline_surface = pygame.Surface((outline_rect.width, outline_rect.height), pygame.SRCALPHA)
                    pygame.draw.rect(outline_surface, (100, 255, 100, 100),
                                     (0, 0, outline_rect.width, outline_rect.height), 2)
                    screen.blit(outline_surface, (ghost_x - 2, ghost_y - 2))
                else:
                    outline_points = [
                        (ghost_x + ghost_width // 2, ghost_y),
                        (ghost_x, ghost_y + ghost_height),
                        (ghost_x + ghost_width, ghost_y + ghost_height)
                    ]
                    pygame.draw.polygon(screen, (100, 255, 100, 150), outline_points, 3)

            # 绘制时间环（可选特效）
            ghost_center_x = ghost_x + ghost_width // 2
            ghost_center_y = ghost_y + ghost_height // 2
            radius = max(ghost_width, ghost_height) // 2 + 8

            # 绘制外环（完整2秒）
            ring_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(ring_surface, (50, 150, 50, 80),
                               (radius, radius), radius, 2)
            screen.blit(ring_surface, (ghost_center_x - radius, ghost_center_y - radius))

            # 绘制时间进度弧（根据历史记录长度）
            if hasattr(self, 'position_history'):
                time_ratio = min(1.0, len(self.position_history) / 120.0)
                if time_ratio > 0:
                    end_angle = 2 * math.pi * time_ratio
                    arc_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.arc(arc_surface, (100, 255, 100, 180),
                                    (0, 0, radius * 2, radius * 2),
                                    0, end_angle, 4)
                    screen.blit(arc_surface, (ghost_center_x - radius, ghost_center_y - radius))

            # 绘制连接线（从玩家到虚影）
            player_center_x = self.x + self.width // 2
            player_center_y = self.y + self.height // 2

            # 计算距离和方向
            dx = ghost_center_x - player_center_x
            dy = ghost_center_y - player_center_y
            distance = max(1, math.sqrt(dx * dx + dy * dy))

            # 绘制虚线连接线
            if distance > 600:  # 只有距离足够远时才绘制连接线
                dash_length = 8
                gap_length = 4
                dash_count = int(distance / (dash_length + gap_length))

                if dash_count > 0:
                    for i in range(dash_count):
                        start_ratio = i / dash_count
                        end_ratio = (i + dash_length / (dash_length + gap_length)) / dash_count

                        start_x = player_center_x + dx * start_ratio
                        start_y = player_center_y + dy * start_ratio
                        end_x = player_center_x + dx * end_ratio
                        end_y = player_center_y + dy * end_ratio

                        pygame.draw.line(screen, (100, 255, 100, 120),
                                         (int(start_x), int(start_y)),
                                         (int(end_x), int(end_y)), 2)

        # ========== 绘制春秋蝉技能残影（现有代码） ==========
        if hasattr(self, 'skill2_active') and self.skill2_active and hasattr(self, 'skill2_afterimages'):
            for afterimage in self.skill2_afterimages:
                if afterimage['alpha'] > 0:
                    if self.image:
                        # 有图像的情况：绘制半透明残影
                        afterimage_surface = self.image.copy()
                        afterimage_surface.set_alpha(afterimage['alpha'])
                        screen.blit(afterimage_surface, (afterimage['x'], afterimage['y']))
                    else:
                        # 无图像的情况：绘制半透明三角形
                        alpha_surface = pygame.Surface((afterimage['width'], afterimage['height']), pygame.SRCALPHA)
                        pygame.draw.polygon(alpha_surface, (100, 200, 255, afterimage['alpha']), [
                            (afterimage['width'] // 2, 0),
                            (0, afterimage['height']),
                            (afterimage['width'], afterimage['height'])
                        ])
                        screen.blit(alpha_surface, (afterimage['x'], afterimage['y']))

        # ========== 绘制闪现技能轨迹（现有代码） ==========
        if hasattr(self, 'skill1_active') and self.skill1_active:
            if hasattr(self, 'skill1_old_pos'):
                if self.image:
                    # 有图像的情况：绘制残影
                    if hasattr(self, 'skill1_old_pos'):
                        old_x, old_y = self.skill1_old_pos['x'], self.skill1_old_pos['y']
                        if old_x != self.x or old_y != self.y:
                            alpha = 255 - (self.skill1_use_time / self.skill1_effect_duration * 255)
                            ghost_image = self.image.copy()
                            ghost_image.set_alpha(int(alpha * 0.5))
                            screen.blit(ghost_image, (old_x, old_y))
                else:
                    # 无图像的情况：绘制轨迹
                    if hasattr(self, 'skill1_old_pos'):
                        old_x, old_y = self.skill1_old_pos['x'], self.skill1_old_pos['y']
                        pygame.draw.line(screen, (0, 200, 255),
                                         (old_x + self.width // 2, old_y + self.height // 2),
                                         (self.x + self.width // 2, self.y + self.height // 2), 3)

        # ========== 绘制玩家主体（现有代码） ==========
        if self.image:
            # 使用图像绘制
            if self.invincible > 0 and self.invincible % 6 < 3:
                # 无敌时闪烁：设置半透明
                temp_image = self.image.copy()
                temp_image.set_alpha(128)  # 50%透明度
                screen.blit(temp_image, (self.x, self.y))
            else:
                screen.blit(self.image, (self.x, self.y))
        else:
            # 回退到原来的颜色绘制逻辑
            if self.invincible > 0 and self.invincible % 6 < 3:
                # 无敌时闪烁
                pygame.draw.polygon(screen, WHITE, [
                    (self.x + self.width // 2, self.y),
                    (self.x, self.y + self.height),
                    (self.x + self.width, self.y + self.height)
                ])
            else:
                pygame.draw.polygon(screen, self.color, [
                    (self.x + self.width // 2, self.y),
                    (self.x, self.y + self.height),
                    (self.x + self.width, self.y + self.height)
                ])

            # 绘制飞机机翼
            if self.invincible <= 0 or self.invincible % 6 >= 3:
                pygame.draw.rect(screen, self.color, (self.x - 10, self.y + 20, 70, 10))

        # ========== 绘制技能激活特效（在玩家主体之后） ==========
        # 闪现技能当前位置闪烁
        if hasattr(self, 'skill1_active') and self.skill1_active:
            if self.skill1_use_time % 6 < 3:  # 闪烁效果
                if self.image:
                    flash_image = self.image.copy()
                    flash_image.set_alpha(128)
                    screen.blit(flash_image, (self.x, self.y))
                else:
                    pygame.draw.polygon(screen, (255, 255, 255, 128), [
                        (self.x + self.width // 2, self.y),
                        (self.x, self.y + self.height),
                        (self.x + self.width, self.y + self.height)
                    ])

        # 春秋蝉技能时间扭曲特效
        if hasattr(self, 'skill2_time_warp_effect') and self.skill2_time_warp_effect:
            if self.skill2_use_time < 30:  # 前0.5秒显示特效
                center_x = self.x + self.width // 2
                center_y = self.y + self.height // 2
                radius = max(self.width, self.height) // 2 + 15

                # 创建扭曲光环表面
                warp_surface = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)

                # 绘制扭曲光环（随时间变化）
                wave = math.sin(pygame.time.get_ticks() * 0.01) * 10
                for i in range(5):
                    alpha = 150 - i * 30
                    pygame.draw.circle(warp_surface, (100, 200, 255, alpha),
                                       (radius * 2, radius * 2),
                                       radius + wave + i * 5, 3)

                screen.blit(warp_surface, (center_x - radius * 2, center_y - radius * 2))

        # ========== 绘制技能准备指示器 ==========
        # 闪现技能准备指示器
        if hasattr(self, 'skill1_ready') and self.skill1_ready:
            self.draw_skill1_indicator()

        # 春秋蝉技能准备指示器（不同颜色和样式）
        if hasattr(self, 'skill2_ready') and self.skill2_ready:
            self.draw_skill2_indicator()
        # =====================================

        # 绘制生命值（这部分保持不变）
        for i in range(self.health):
            pygame.draw.rect(screen, RED, (10 + i * 35, 10, 30, 20))
            pygame.draw.rect(screen, WHITE, (10 + i * 35, 10, 30, 20), 2)

        # 绘制分数和伤害（这部分保持不变）
        score_text = FONTS["normal"].render(f"得分：{self.score}", True, WHITE)
        screen.blit(score_text, (WIDTH - 150, 10))

        damage_text = FONTS["small"].render(f"子弹伤害：{self.bullet_damage}", True, YELLOW)
        screen.blit(damage_text, (WIDTH - 150, 40))

        # ========== 绘制时停领域 ==========
        if self.time_field_active and self.time_field_center:
            center_x, center_y = self.time_field_center

            # 1. 绘制领域背景（半透明蓝色圆盘）
            field_surface = pygame.Surface((self.time_field_radius * 2, self.time_field_radius * 2), pygame.SRCALPHA)

            # 渐变填充（中心亮，边缘暗）
            for r in range(self.time_field_radius, 0, -2):
                alpha = int(30 * (r / self.time_field_radius))
                pygame.draw.circle(field_surface, (0, 100, 200, alpha),
                                   (self.time_field_radius, self.time_field_radius), r)

            screen.blit(field_surface, (center_x - self.time_field_radius,
                                        center_y - self.time_field_radius))

            # 2. 绘制领域边界（脉冲光环）
            pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.5
            border_radius = self.time_field_radius + pulse * 10

            # 外环 - 创建透明表面来绘制带透明度的圆环
            border_surface = pygame.Surface((int(border_radius * 2), int(border_radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(border_surface, (0, 200, 255, 150),
                               (int(border_radius), int(border_radius)), int(border_radius), 3)
            screen.blit(border_surface, (center_x - border_radius, center_y - border_radius))

            # 内环
            inner_border_surface = pygame.Surface((int((border_radius - 5) * 2), int((border_radius - 5) * 2)),
                                                  pygame.SRCALPHA)
            pygame.draw.circle(inner_border_surface, (100, 220, 255, 200),
                               (int(border_radius - 5), int(border_radius - 5)), int(border_radius - 5), 2)
            screen.blit(inner_border_surface, (center_x - border_radius + 5, center_y - border_radius + 5))

            # 3. 绘制时间符号（时钟图标）
            clock_radius = 20
            current_time = pygame.time.get_ticks() * 0.001

            # 时钟外圈 - 使用RGB颜色（不带透明度）
            pygame.draw.circle(screen, (255, 255, 255),
                               (int(center_x), int(center_y)), clock_radius, 2)

            # 时钟指针
            for i, (length, width) in enumerate([(15, 2), (10, 1)]):  # 时针和分针
                angle = current_time * (0.5 if i == 0 else 3)  # 时针慢，分针快
                end_x = center_x + math.cos(angle) * length
                end_y = center_y + math.sin(angle) * length
                pygame.draw.line(screen, (255, 255, 255),
                                 (center_x, center_y), (end_x, end_y), width)

            # 4. 绘制领域粒子 - 这部分已正确使用带透明度的表面

            # 5. 绘制时间进度环
            progress = self.time_field_use_time / self.time_field_duration
            if progress < 0.95:  # 最后5%不显示，表示即将消失
                # 使用半透明表面绘制进度环
                progress_surface = pygame.Surface((int((self.time_field_radius + 10) * 2),
                                                   int((self.time_field_radius + 10) * 2)), pygame.SRCALPHA)

                rect = pygame.Rect(0, 0,
                                   int((self.time_field_radius + 10) * 2),
                                   int((self.time_field_radius + 10) * 2))

                end_angle = 2 * math.pi * (1 - progress)
                pygame.draw.arc(progress_surface, (255, 255, 100, 200),
                                rect, end_angle, 2 * math.pi, 4)

                screen.blit(progress_surface,
                            (center_x - self.time_field_radius - 10,
                             center_y - self.time_field_radius - 10))

        # =====================================

    def draw_skill1_indicator(self):
        """绘制闪现技能准备指示器（蓝色发光效果）"""
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2

        # 绘制多层发光圆环
        for i in range(3):
            radius = max(self.width, self.height) // 2 + 5 + i * 2
            alpha = 100 - i * 30

            # 创建半透明表面
            indicator_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            # 根据时间脉冲效果
            pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) * 0.5  # 0到1的脉冲
            pulse_radius = int(radius * (0.9 + pulse * 0.2))

            # 绘制圆环（蓝色）
            pygame.draw.circle(indicator_surface, (0, 200, 255, alpha),
                               (radius, radius), pulse_radius, 2)

            # 绘制到屏幕
            screen.blit(indicator_surface, (center_x - radius, center_y - radius))

        # 绘制中心闪烁点（蓝色）
        blink = (pygame.time.get_ticks() % 1000) < 500
        if blink:
            pygame.draw.circle(screen, (255, 255, 100), (center_x, center_y), 4)

    def draw_skill2_indicator(self):
        """绘制春秋蝉技能准备指示器（绿色发光效果）"""
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2

        # 绘制多层发光圆环（绿色）
        for i in range(3):
            radius = max(self.width, self.height) // 2 + 8 + i * 3  # 比闪现技能大一点
            alpha = 80 - i * 20  # 稍微透明一些

            # 创建半透明表面
            indicator_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            # 根据时间脉冲效果（不同的频率）
            pulse = (math.sin(pygame.time.get_ticks() * 0.003) + 1) * 0.5  # 更慢的脉冲
            pulse_radius = int(radius * (0.85 + pulse * 0.3))  # 更大的波动范围

            # 绘制圆环（绿色）
            pygame.draw.circle(indicator_surface, (100, 255, 100, alpha),
                               (radius, radius), pulse_radius, 2)

            # 绘制到屏幕
            screen.blit(indicator_surface, (center_x - radius, center_y - radius))

        # 绘制时光沙漏符号
        hourglass_size = 12
        # 上半部分
        pygame.draw.polygon(screen, (100, 255, 100), [
            (center_x, center_y - hourglass_size // 2),
            (center_x - hourglass_size // 3, center_y),
            (center_x + hourglass_size // 3, center_y)
        ])
        # 下半部分
        pygame.draw.polygon(screen, (100, 255, 100), [
            (center_x, center_y + hourglass_size // 2),
            (center_x - hourglass_size // 3, center_y),
            (center_x + hourglass_size // 3, center_y)
        ])
        # 中间连接点
        pygame.draw.circle(screen, (100, 255, 100), (center_x, center_y), 2)
    def move(self, keys):
        if keys[pygame.K_a] and self.x > 0:
            self.x -= self.speed
        if keys[pygame.K_d] and self.x < WIDTH - self.width:
            self.x += self.speed
        if keys[pygame.K_w] and self.y > 0:
            self.y -= self.speed
        if keys[pygame.K_s] and self.y < HEIGHT - self.height:
            self.y += self.speed

    def shoot(self):
        if self.shoot_cooldown == 0:
            self.bullets.append(Bullet(
                self.x + self.width // 2 - 2.5,
                self.y,
                self.bullet_damage,
                self.game_resources  # 传入资源管理器
            ))
            self.shoot_cooldown = 10  # 设置射击冷却时间

            # 播放射击音效
            if hasattr(self.game_resources, 'play_sound'):
                self.game_resources.play_sound('shoot')
            return True  # 返回成功射击
        return False  # 返回未能射击（冷却中）

    def update(self):

        self.update_position_history()

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        if self.invincible > 0:
            self.invincible -= 1

        # 自动射击：每次update检查冷却，冷却完成就射击
        if self.shoot_cooldown == 0:
            self.shoot()  # 这会设置新的冷却时间

        self.update_skill()   #定仙游技能
        self.update_skill2()  # 春秋蝉技能

        # ========== 更新时停领域技能 ==========
        self.update_time_field()
        # ===================================

        # 更新子弹
        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.y < 0:
                self.bullets.remove(bullet)

    def update_rewind_ghost(self):
        """更新要闪回的虚影位置"""
        # 更新计时器
        self.ghost_update_timer += 1
        self.ghost_blink_timer += 1

        # 如果技能2未就绪，不显示虚影
        if not self.skill2_ready:
            self.ghost_visible = False
            return

        # 定期更新虚影位置（每30帧/0.5秒）
        if self.ghost_update_timer >= self.ghost_update_interval:
            self.ghost_update_timer = 0

            # 获取2秒前（120帧前）的位置
            if len(self.position_history) >= 120:
                target_frame = len(self.position_history) - 120
                target_pos = self.position_history[target_frame]

                # 更新虚影位置
                self.rewind_ghost = {
                    'x': target_pos['x'],
                    'y': target_pos['y'],
                    'width': self.width,
                    'height': self.height,
                    'alpha': 180  # 初始透明度
                }
                self.ghost_visible = True

        # 更新虚影透明度（闪烁效果）
        if self.ghost_visible and self.rewind_ghost:
            # 呼吸效果：透明度在120-220之间变化
            pulse = (math.sin(self.ghost_blink_timer * 0.05) + 1) * 0.5  # 0到1
            self.ghost_alpha = int(120 + pulse * 100)
            self.rewind_ghost['alpha'] = self.ghost_alpha

    def update_position_history(self):
        """更新玩家位置历史记录"""
        # 记录当前位置
        current_pos = {
            'x': self.x,
            'y': self.y,
            'health': self.health,
            'frame': self.skill2_use_time if hasattr(self, 'skill2_use_time') else 0
        }

        self.position_history.append(current_pos)



        # 保持历史记录不超过最大长度
        if len(self.position_history) > self.max_history_length:
            self.position_history.pop(0)
            # ========== 更新春秋蝉虚影 ==========
        self.update_rewind_ghost()
        # ===================================


    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def take_damage(self):
        if self.invincible <= 0:
            self.health -= 1
            self.invincible = 30  # 0.5秒无敌时间（60帧/秒）
            return True
        return False

    def increase_bullet_damage(self):
        self.bullet_damage += 1


# 在游戏结束或重新开始时清理时停效果
def cleanup_time_field_effects(player):
    """清理所有时停效果"""
    if player and hasattr(player, '_time_field_affected_enemies'):
        for enemy in player._time_field_affected_enemies:
            if hasattr(enemy, 'is_slowed') and enemy.is_slowed:
                if hasattr(enemy, 'original_speed'):
                    enemy.speed = enemy.original_speed
                enemy.is_slowed = False
                enemy.slow_factor = 1.0

                # 恢复子弹速度
                if hasattr(enemy, 'bullets'):
                    for bullet in enemy.bullets:
                        if hasattr(bullet, 'original_speed'):
                            bullet.speed = bullet.original_speed

        player._time_field_affected_enemies.clear()
# 子弹类
class Bullet:
    def __init__(self, x, y, damage=1, game_resources=None):
        self.x = x
        self.y = y
        self.width = 5
        self.height = 15
        self.speed = 10
        self.color = YELLOW
        self.damage = damage
        self.game_resources = game_resources

        # 使用游戏资源中的图像
        if game_resources and hasattr(game_resources, 'images') and 'bullet' in game_resources.images:
            self.image = game_resources.images['bullet']
        else:
            self.image = None
    def draw(self):
        # 根据伤害值调整子弹大小和颜色
        bullet_width = self.width + (self.damage - 1) * 2
        bullet_height = self.height + (self.damage - 1) * 3

        # 伤害越高颜色越亮
        color_intensity = min(255, 200 + (self.damage - 1) * 20)
        bullet_color = (color_intensity, color_intensity, max(0, 150 - (self.damage - 1) * 30))

        pygame.draw.rect(screen, bullet_color, (self.x - (bullet_width - self.width) // 2,
                                                self.y, bullet_width, bullet_height))

    def update(self):
        self.y -= self.speed

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


# 敌机类
class Enemy:
    def __init__(self, level=1, game_resources=None, is_boss=False, boss_level=1):
        self.game_resources = game_resources
        self.is_boss = is_boss
        self.boss_level = boss_level

        if self.is_boss:
            # ========== BOSS敌人 ==========
            self.width = 80
            self.height = 80
            # 初始位置在顶部中间
            self.x = WIDTH // 2 - self.width // 2
            self.y = 50  # 在上方

            # Boss属性（随boss_level递增）
            self.base_speed = 3.0 + (boss_level - 1) * 0.5  # 初始3，每次+0.5
            self.speed = self.base_speed
            self.original_speed = self.speed  # 添加：保存原始速度用于时停
            self.level = 999  # 设为很高，表示Boss

            # Boss生命值（初始50，每次+30）
            self.base_health = 50 + (boss_level - 1) * 30
            self.health = self.base_health
            self.max_health = self.base_health

            # Boss伤害（初始2，每次+1）
            self.damage = 2 + (boss_level - 1) * 1

            # Boss颜色（暗红色）
            self.color = (180, 0, 0)

            # Boss移动参数
            self.move_direction = random.choice([-1, 1])  # 初始移动方向
            self.move_counter = 0
            self.move_duration = random.randint(60, 120)  # 移动持续时间

            # ========== Boss攻击参数 ==========
            self.fire_counter = 0
            self.fire_rate = max(30, 90 - boss_level * 10)  # 随等级提高射速
            self.bullets = []  # Boss子弹列表
            # =================================

            # Boss分数
            self.score = 1000 * boss_level

            # Boss图像（如果有）
            if game_resources and hasattr(game_resources, 'images') and 'boss' in game_resources.images:
                self.image = game_resources.images['boss']
            else:
                self.image = None

            # ========== 时停相关属性（Boss）==========
            self.is_slowed = False  # 是否被时停影响
            self.slow_factor = 1.0  # 减速因子（1.0为正常速度）
            self.original_speed_set = False  # 标志是否已保存原始速度

        else:
            # ========== 普通敌人 ==========
            self.width = 40
            self.height = 40
            self.x = random.randint(0, WIDTH - self.width)
            self.y = random.randint(-100, -40)
            self.base_speed = random.uniform(1.0, 2.0)
            self.speed = self.base_speed * (1 + 0.2 * level)  # 速度随等级提高
            self.original_speed = self.speed  # 添加：保存原始速度用于时停
            self.color = RED
            self.level = level
            self.health = 1
            self.max_health = 1
            self.direction_change_timer = random.randint(30, 90)

            if game_resources and hasattr(game_resources, 'images') and 'enemy' in game_resources.images:
                self.image = game_resources.images['enemy']
            else:
                self.image = None

            # ========== 时停相关属性（普通敌人）==========
            self.is_slowed = False  # 是否被时停影响
            self.slow_factor = 1.0  # 减速因子（1.0为正常速度）
            self.original_speed_set = False  # 标志是否已保存原始速度

    def draw(self):
        if self.is_boss:
            # ========== 绘制BOSS ==========
            if self.image:
                screen.blit(self.image, (self.x, self.y))
            else:
                # 绘制Boss图形（如果没有图片）
                # 主体（红色圆角矩形）
                pygame.draw.rect(screen, self.color,
                                 (self.x, self.y, self.width, self.height),
                                 border_radius=20)

                # 内部装饰（深红色）
                inner_rect = pygame.Rect(self.x + 10, self.y + 10,
                                         self.width - 20, self.height - 20)
                pygame.draw.rect(screen, (120, 0, 0), inner_rect, border_radius=10)

                # 眼睛（黄色）
                pygame.draw.circle(screen, YELLOW,
                                   (self.x + self.width // 3, self.y + self.height // 3), 6)
                pygame.draw.circle(screen, YELLOW,
                                   (self.x + 2 * self.width // 3, self.y + self.height // 3), 6)

                # 嘴巴（白色弧线）
                pygame.draw.arc(screen, WHITE,
                                (self.x + 20, self.y + 50, self.width - 40, 20),
                                0, 3.14, 3)

                # 绘制Boss等级
                font = pygame.font.Font(None, 24)
                level_text = font.render(f"Boss Lv{self.boss_level}", True, WHITE)
                text_rect = level_text.get_rect(center=(self.x + self.width // 2,
                                                        self.y + self.height + 15))
                screen.blit(level_text, text_rect)

            # ========== 绘制BOSS血条 ==========
            # 血条背景
            bar_width = self.width + 20
            bar_x = self.x - 10
            bar_y = self.y - 25
            bar_height = 10

            pygame.draw.rect(screen, (100, 0, 0),
                             (bar_x, bar_y, bar_width, bar_height))

            # 当前血量
            health_ratio = self.health / self.max_health
            current_width = int(bar_width * health_ratio)

            # 根据血量改变颜色
            if health_ratio > 0.6:
                health_color = (0, 255, 0)  # 绿色
            elif health_ratio > 0.3:
                health_color = (255, 255, 0)  # 黄色
            else:
                health_color = (255, 0, 0)  # 红色

            pygame.draw.rect(screen, health_color,
                             (bar_x, bar_y, current_width, bar_height))

            # 血条边框
            pygame.draw.rect(screen, WHITE,
                             (bar_x, bar_y, bar_width, bar_height), 1)

            # 血量文字
            font = pygame.font.Font(None, 18)
            hp_text = font.render(f"{self.health}/{self.max_health}", True, WHITE)
            screen.blit(hp_text, (bar_x + bar_width // 2 - hp_text.get_width() // 2,
                                  bar_y - 15))

            # ========== 绘制Boss子弹 ==========

            for bullet in self.bullets:
                if hasattr(bullet, 'draw'):
                    # 使用BossBullet类的draw方法
                    bullet.draw()
                else:
                    # 兼容旧的字典格式（备份方案）
                    pygame.draw.rect(screen, (255, 100, 100),
                                     (bullet['x'], bullet['y'],
                                      bullet['width'], bullet['height']))

        else:
            # ========== 绘制普通敌人 ==========
            if self.image:
                screen.blit(self.image, (self.x, self.y))

                # 高等级敌机特殊标记
                if self.level >= 3:
                    pygame.draw.circle(screen, ORANGE,
                                       (int(self.x + self.width // 2), int(self.y + self.height // 2)), 8, 2)
            else:
                # 原来的绘制逻辑
                color_intensity = min(255, 150 + self.level * 20)
                enemy_color = (color_intensity, max(0, 100 - self.level * 20), max(0, 100 - self.level * 20))
                pygame.draw.polygon(screen, enemy_color, [
                    (self.x + self.width // 2, self.y + self.height),
                    (self.x, self.y),
                    (self.x + self.width, self.y)
                ])
                pygame.draw.rect(screen, enemy_color, (self.x - 5, self.y + 15, 50, 8))

                if self.level >= 3:
                    pygame.draw.circle(screen, ORANGE,
                                       (int(self.x + self.width // 2), int(self.y + self.height // 2)), 8, 2)

    def update(self):
        if self.is_boss:
            # ========== BOSS移动逻辑 ==========
            self.move_counter += 1
            self.fire_counter += 1

            # 左右移动
            self.x += self.speed * self.move_direction

            # 边界检查（Boss只在屏幕上半部分移动）
            if self.x < 0:
                self.x = 0
                self.move_direction = 1  # 向右
                self.move_counter = 0
            elif self.x > WIDTH - self.width:
                self.x = WIDTH - self.width
                self.move_direction = -1  # 向左
                self.move_counter = 0

            # 随机改变方向
            if self.move_counter >= self.move_duration and random.random() < 0.3:
                self.move_direction *= -1
                self.move_duration = random.randint(60, 120)
                self.move_counter = 0

            # Boss不会向下移动，保持在 y=50 位置附近轻微上下浮动
            if random.random() < 0.02:  # 2%概率轻微上下浮动
                self.y += random.uniform(-1, 1)
                self.y = max(30, min(100, self.y))  # 限制在30-100范围内

            # ========== 更新Boss子弹 ==========
            self.update_bullets()

        else:
            # ========== 普通敌人移动逻辑 ==========
            self.y += self.speed

            # 敌机随机移动
            self.direction_change_timer -= 1
            if self.direction_change_timer <= 0:
                self.direction_change_timer = random.randint(30, 90)

            # 轻微随机左右移动
            if random.random() < 0.1:  # 10%概率改变方向
                self.x += random.uniform(-2, 2) * (1 + 0.1 * self.level)

            # 边界检查
            if self.x < 0:
                self.x = 0
            if self.x > WIDTH - self.width:
                self.x = WIDTH - self.width

    def update_bullets(self):
        """更新Boss子弹"""
        if self.is_boss:
            for bullet in self.bullets[:]:
                # 如果bullet是BossBullet对象，调用其update方法
                if hasattr(bullet, 'update'):
                    bullet.update()

                    # 检查是否出界
                    if hasattr(bullet, 'is_out_of_screen') and bullet.is_out_of_screen():
                        self.bullets.remove(bullet)
                else:
                    # 兼容旧的字典格式子弹
                    # 根据方向移动子弹
                    if 'direction' in bullet:
                        # 有特定方向的子弹
                        bullet['x'] += bullet['speed'] * bullet['direction'][0]
                        bullet['y'] += bullet['speed'] * bullet['direction'][1]
                    else:
                        # 向下移动的子弹
                        bullet['y'] += bullet['speed']

                    # 检查子弹是否出界
                    if (bullet['y'] > HEIGHT or
                            bullet['x'] < 0 or
                            bullet['x'] > WIDTH or
                            bullet['y'] < 0):
                        self.bullets.remove(bullet)

    def can_fire(self):
        """检查是否可以发射子弹"""
        if self.is_boss:
            return self.fire_counter >= self.fire_rate
        return False

    def fire(self):
        """Boss发射子弹"""
        if self.is_boss and self.can_fire():
            # 重置开火计数器
            self.fire_counter = 0

            # 创建BossBullet对象
            new_bullets = []

            # 基础向下子弹
            new_bullets.append(BossBullet(
                self.x + self.width // 2 - 3,
                self.y + self.height,
                direction=(0, 1),  # 向下
                boss_level=self.boss_level,
                game_resources=self.game_resources
            ))

            # 随着Boss等级提高，增加更多子弹
            if self.boss_level >= 2:
                # 左侧斜向子弹
                new_bullets.append(BossBullet(
                    self.x + self.width // 4 - 3,
                    self.y + self.height,
                    direction=(-0.3, 1),  # 左下
                    boss_level=self.boss_level,
                    game_resources=self.game_resources
                ))

                # 右侧斜向子弹
                new_bullets.append(BossBullet(
                    self.x + 3 * self.width // 4 - 3,
                    self.y + self.height,
                    direction=(0.3, 1),  # 右下
                    boss_level=self.boss_level,
                    game_resources=self.game_resources
                ))

            if self.boss_level >= 3:
                # 水平方向子弹（向两侧发射）
                new_bullets.append(BossBullet(
                    self.x,
                    self.y + self.height // 2,
                    direction=(-1, 0),  # 向左
                    boss_level=self.boss_level,
                    game_resources=self.game_resources
                ))

                new_bullets.append(BossBullet(
                    self.x + self.width,
                    self.y + self.height // 2,
                    direction=(1, 0),  # 向右
                    boss_level=self.boss_level,
                    game_resources=self.game_resources
                ))

            # 如果Boss等级>=4，增加更复杂的弹幕
            if self.boss_level >= 4:
                # 8方向弹幕
                directions = [
                    (0, 1), (0.7, 0.7), (1, 0), (0.7, -0.7),
                    (0, -1), (-0.7, -0.7), (-1, 0), (-0.7, 0.7)
                ]
                for dx, dy in directions:
                    new_bullets.append(BossBullet(
                        self.x + self.width // 2 - 3,
                        self.y + self.height // 2,
                        direction=(dx, dy),
                        boss_level=self.boss_level,
                        game_resources=self.game_resources
                    ))

            # 添加所有新子弹到列表
            self.bullets.extend(new_bullets)

            # 播放射击音效（如果资源管理器有该音效）
            if self.game_resources and hasattr(self.game_resources, 'play_sound'):
                self.game_resources.play_sound('shoot')  # 可以使用特殊的Boss射击音效



    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def take_damage(self, damage):
        """受到伤害"""
        self.health -= damage
        return self.health <= 0

    def get_score(self):
        """获取击落分数"""
        if self.is_boss:
            return self.score
        else:
            return 100 * self.level  # 普通敌人分数

    def is_out_of_screen(self):
        """检查是否超出屏幕"""
        if self.is_boss:
            return False  # Boss不会自动超出屏幕
        else:
            return self.y > HEIGHT

    def get_bullet_rects(self):
        """获取Boss子弹的矩形列表（用于碰撞检测）"""
        if self.is_boss:
            bullet_rects = []
            for bullet in self.bullets:
                if hasattr(bullet, 'get_rect'):
                    # BossBullet对象
                    bullet_rects.append(bullet.get_rect())
                else:
                    # 旧的字典格式
                    bullet_rects.append(pygame.Rect(
                        bullet['x'], bullet['y'],
                        bullet['width'], bullet['height']
                    ))
            return bullet_rects
        return []

# 精英敌机类（更难对付）
class EliteEnemy(Enemy):
    def __init__(self, level=1, game_resources=None):

        # 先调用父类的初始化，传入 game_resources
        super().__init__(level, game_resources,is_boss=False,boss_level=1)

        # 然后修改精英敌机特有的属性s
        self.width = 60
        self.height = 50
        self.base_speed = random.uniform(0.8, 1.5)
        self.speed = self.base_speed * (1 + 0.05 * level)
        self.color = PURPLE
        self.health = 2
        self.max_health = 2
        self.shoot_timer = random.randint(60, 120)
        self.bullets = []

        # 如果需要特殊的精英敌机图像
        if game_resources and hasattr(game_resources, 'images') and 'elite_enemy' in game_resources.images:
            self.image = game_resources.images['elite_enemy']
        # 如果没有特殊图像，使用父类的 enemy 图像

    def draw(self):
        if self.image:
            # 使用图像绘制
            screen.blit(self.image, (self.x, self.y))

            # 可以添加精英敌机特有的视觉效果
            if self.health < self.max_health:
                # 绘制生命条
                bar_width = 40
                bar_height = 5
                health_ratio = self.health / self.max_health

                # 绘制生命条背景
                pygame.draw.rect(screen, RED,
                                 (self.x + self.width // 2 - bar_width // 2, self.y - 10, bar_width, bar_height))
                # 绘制当前生命值
                pygame.draw.rect(screen, GREEN, (
                    self.x + self.width // 2 - bar_width // 2, self.y - 10, bar_width * health_ratio, bar_height))

                # 添加精英敌机特殊效果（例如发光边缘）
                if self.health <= self.max_health // 2:  # 血量低于一半时
                    # 绘制发光边框
                    glow_surface = pygame.Surface((self.width + 4, self.height + 4), pygame.SRCALPHA)
                    glow_color = (255, 100, 255, 100)  # 紫色发光
                    pygame.draw.polygon(glow_surface, glow_color, [
                        (self.width // 2 + 2, 2),
                        (self.width + 2, self.height // 2 + 2),
                        (self.width // 2 + 2, self.height + 2),
                        (2, self.height // 2 + 2)
                    ])
                    screen.blit(glow_surface, (self.x - 2, self.y - 2), special_flags=pygame.BLEND_ALPHA_SDL2)
        else:
            # 回退到原来的颜色绘制逻辑
            # 绘制精英敌机（菱形）
            points = [
                (self.x + self.width // 2, self.y),  # 上
                (self.x + self.width, self.y + self.height // 2),  # 右
                (self.x + self.width // 2, self.y + self.height),  # 下
                (self.x, self.y + self.height // 2)  # 左
            ]
            pygame.draw.polygon(screen, PURPLE, points)

            # 绘制生命条
            if self.health < self.max_health:
                bar_width = 40
                bar_height = 5
                health_ratio = self.health / self.max_health
                pygame.draw.rect(screen, RED,
                                 (self.x + self.width // 2 - bar_width // 2, self.y - 10, bar_width, bar_height))
                pygame.draw.rect(screen, GREEN, (
                    self.x + self.width // 2 - bar_width // 2, self.y - 10, bar_width * health_ratio, bar_height))

                # 血量低时添加警告效果
                if self.health <= self.max_health // 2:
                    # 绘制闪烁边框
                    if pygame.time.get_ticks() % 500 < 250:
                        pygame.draw.polygon(screen, ORANGE, points, 3)
    def update(self):
        super().update()

        # 精英敌机可以射击
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            # 注意：EnemyBullet现在只需要2个参数(x, y)，难度级别在构造函数内部处理
            # 传递精英敌机的等级作为难度级别
            self.bullets.append(EnemyBullet(
                self.x + self.width // 2 - 2.5,
                self.y + self.height,
                difficulty_level=self.level,  # 添加难度级别参数
                game_resources=self.game_resources  # 传递资源管理器
            ))
            self.shoot_timer = random.randint(80, 160)

    # 更新子弹
        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.y > HEIGHT:
                self.bullets.remove(bullet)


# 追踪敌机类（新敌人3）
class TrackingEnemy(Enemy):
    def __init__(self, level=1, game_resources=None):
        # 先调用父类的初始化，传入 game_resources
        super().__init__(level, game_resources,is_boss=False,boss_level=1)

        # 然后修改追踪敌机特有的属性
        self.width = 45
        self.height = 45
        self.base_speed = random.uniform(0.6, 1.2)
        self.speed = self.base_speed * (1 + 0.05 * level)
        self.color = CYAN
        self.health = 3 * (1 + 0.15 * level)  # 初始3HP，随等级增加
        self.max_health = self.health  # 最大血量等于当前血量
        self.tracking_frames = 15  # 追踪15帧
        self.tracking_counter = 0
        self.target_x = WIDTH // 2
        self.target_y = HEIGHT // 2
        self.last_tracking_time = 0
        self.life_timer = 0  # 新增：生命周期计时器
        self.max_life_time = 900  # 最大生命周期900帧=15秒（60帧/秒）
        self.flash_timer = 0  # 新增：闪烁计时器
        self.flash_interval = 30  # 新增：闪烁间隔

        # 如果需要特殊的追踪敌机图像
        if game_resources and hasattr(game_resources, 'images') and 'tracking_enemy' in game_resources.images:
            self.image = game_resources.images['tracking_enemy']
        # 如果没有特殊图像，使用父类的 enemy 图像

    def draw(self):
        if self.image:
            # 使用图像绘制
            center_x = self.x + self.width // 2
            center_y = self.y + self.height // 2

            # 计算生命剩余比例
            life_ratio = 1.0 - (self.life_timer / self.max_life_time)

            # 根据剩余生命时间调整透明度
            if life_ratio < 0.3:  # 最后3秒开始闪烁
                self.flash_timer += 1
                if self.flash_timer % self.flash_interval < self.flash_interval // 2:
                    # 闪烁期间绘制，但透明度变化
                    alpha = int(128 + 127 * (self.flash_timer % self.flash_interval) / (self.flash_interval // 2))
                    temp_image = self.image.copy()
                    temp_image.set_alpha(alpha)
                    screen.blit(temp_image, (self.x, self.y))
                else:
                    # 闪烁期间不绘制
                    return
            else:
                # 正常绘制
                screen.blit(self.image, (self.x, self.y))

            # 根据剩余生命时间调整图像颜色（可选）
            if life_ratio < 0.5:
                # 创建半透明覆盖层使图像变暗
                overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                darken_factor = int(255 * (1 - life_ratio))
                overlay.fill((0, 0, 0, darken_factor))
                screen.blit(overlay, (self.x, self.y), special_flags=pygame.BLEND_RGBA_MULT)
        else:
            # 回退到原来的颜色绘制逻辑
            center_x = self.x + self.width // 2
            center_y = self.y + self.height // 2
            radius = min(self.width, self.height) // 2

            # 计算生命剩余比例
            life_ratio = 1.0 - (self.life_timer / self.max_life_time)

            # 根据剩余生命时间调整透明度或颜色
            if life_ratio < 0.3:  # 最后3秒开始闪烁
                self.flash_timer += 1
                if self.flash_timer % self.flash_interval < self.flash_interval // 2:
                    # 闪烁期间绘制
                    pass
                else:
                    # 闪烁期间不绘制
                    return

            # 根据剩余生命时间调整颜色
            if life_ratio < 0.5:
                # 后半段时间颜色变暗
                color_factor = life_ratio * 2  # 0.0到1.0
                current_color = (
                    int(self.color[0] * color_factor),
                    int(self.color[1] * color_factor),
                    int(self.color[2] * color_factor)
                )
            else:
                current_color = self.color

            # 绘制八边形
            points = []
            for i in range(8):
                angle = math.pi * i / 4
                px = center_x + radius * math.cos(angle)
                py = center_y + radius * math.sin(angle)
                points.append((px, py))

            pygame.draw.polygon(screen, current_color, points)

        # 以下部分两种绘制方式都需要（生命条、时间环等）
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        radius = min(self.width, self.height) // 2
        life_ratio = 1.0 - (self.life_timer / self.max_life_time)

        # 绘制生命时间指示环
        if life_ratio < 0.7:  # 最后7秒显示时间环
            # 绘制背景环
            pygame.draw.circle(screen, (50, 50, 50), (center_x, center_y), radius + 8, 3)
            # 绘制剩余时间环（从绿色到红色）
            ring_color = (
                int(255 * (1 - life_ratio)),  # R: 随时间变红
                int(255 * life_ratio),  # G: 随时间变暗
                0  # B: 固定为0
            )
            # 计算圆弧角度（0到2π）
            end_angle = 2 * math.pi * life_ratio
            # 绘制圆弧表示剩余时间
            pygame.draw.arc(screen, ring_color,
                            (center_x - radius - 8, center_y - radius - 8,
                             (radius + 8) * 2, (radius + 8) * 2),
                            0, end_angle, 3)

        # 绘制追踪指示器
        if self.tracking_counter > 0:
            pygame.draw.circle(screen, ORANGE, (center_x, center_y), radius + 5, 2)

        # 绘制生命条
        bar_width = 40
        bar_height = 5
        health_ratio = self.health / self.max_health
        pygame.draw.rect(screen, RED,
                         (self.x + self.width // 2 - bar_width // 2, self.y - 10, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (
            self.x + self.width // 2 - bar_width // 2, self.y - 10, bar_width * health_ratio, bar_height))

        # 显示血量
        health_int = int(self.health)  # 确保显示整数
        health_text = FONTS["small"].render(str(health_int), True, WHITE)
        screen.blit(health_text, (self.x + self.width // 2 - health_text.get_width() // 2,
                                  self.y + self.height // 2 - health_text.get_height() // 2))

        # 显示剩余时间（最后5秒显示）
        if self.max_life_time - self.life_timer <= 300:  # 最后5秒
            remaining_time = (self.max_life_time - self.life_timer) // 60
            time_text = FONTS["small"].render(f"{remaining_time}s", True, YELLOW)
            screen.blit(time_text, (self.x + self.width // 2 - time_text.get_width() // 2,
                                    self.y - 25))

    def update(self, player_x, player_y, game_timer):
        # 更新生命周期计时器
        self.life_timer += 1

        # 检查是否超过生命周期
        if self.life_timer >= self.max_life_time:
            # 生命周期结束，自动消失（返回True表示需要移除）
            return True

        # 每60秒（3600帧）增加1点血量
        if game_timer % 3600 == 0 and game_timer > 0:
            if self.health < 10:  # 最大血量限制为10
                self.health += 1
                self.max_health += 1

        # 更新追踪逻辑
        self.last_tracking_time += 1

        # 每15帧重新锁定目标
        if self.last_tracking_time >= 15:
            self.target_x = player_x
            self.target_y = player_y
            self.last_tracking_time = 0
            self.tracking_counter = self.tracking_frames

        # 追踪期间朝目标移动
        if self.tracking_counter > 0:
            dx = self.target_x - (self.x + self.width // 2)
            dy = self.target_y - (self.y + self.height // 2)
            distance = max(0.1, math.sqrt(dx * dx + dy * dy))

            # 归一化方向向量
            dx /= distance
            dy /= distance

            # 向目标移动
            self.x += dx * self.speed * 1.5  # 追踪时速度更快
            self.y += dy * self.speed * 1.5
            self.tracking_counter -= 1
        else:
            # 非追踪期间正常下落
            self.y += self.speed

        # 边界检查
        if self.x < 0:
            self.x = 0
        if self.x > WIDTH - self.width:
            self.x = WIDTH - self.width

        return False  # 返回False表示不需要移除

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


# 敌机子弹类
# 在 EnemyBullet.__init__() 中添加：
class EnemyBullet:
    def __init__(self, x, y, difficulty_level=1, game_resources=None):
        self.game_resources = game_resources
        self.x = x
        self.y = y
        self.width = 5
        self.height = 15
        self.speed = 5 + (difficulty_level - 1) // 10
        self.original_speed = self.speed  # 添加：保存原始速度
        self.difficulty_level = difficulty_level
        self.damage = 1 + (difficulty_level - 1) // 10
        self.color = self.get_color_by_damage()

        # 使用游戏资源中的图像（可能没有专门的敌机子弹图像，可以使用普通子弹图像）
        if game_resources and hasattr(game_resources, 'images'):
            # 尝试加载敌机子弹图像
            if 'enemy_bullet' in game_resources.images:
                self.image = game_resources.images['enemy_bullet']
            # 如果没有专门的敌机子弹图像，使用普通子弹图像
            elif 'bullet' in game_resources.images:
                self.image = game_resources.images['bullet']
            else:
                self.image = None
        else:
            self.image = None

    def get_color_by_damage(self):
        """根据伤害值获取子弹颜色"""
        # 保持原来的颜色逻辑
        damage = self.damage
        if damage == 1:
            return ORANGE  # (255, 165, 0)
        elif damage == 2:
            return (255, 100, 0)  # 深橙色
        elif damage == 3:
            return (255, 50, 0)  # 橙红色
        elif damage == 4:
            return (220, 0, 0)  # 暗红色
        else:  # damage >= 5
            return (180, 0, 0)  # 深红色

    def draw(self):
        if self.image:
            # 使用图像绘制
            screen.blit(self.image, (self.x, self.y))

            # 根据伤害值调整图像（如果需要）
            if self.damage >= 3:
                # 高伤害子弹可以添加发光效果
                glow_surface = pygame.Surface((self.width + 4, self.height + 6), pygame.SRCALPHA)
                glow_color = (255, 200, 100, 100)  # 半透明的发光颜色
                pygame.draw.rect(glow_surface, glow_color, (0, 0, glow_surface.get_width(), glow_surface.get_height()),
                                 border_radius=2)
                screen.blit(glow_surface, (self.x - 2, self.y - 3), special_flags=pygame.BLEND_ALPHA_SDL2)

            if self.damage >= 5:
                # 绘制火焰尾迹
                flame_points = [
                    (self.x + self.width // 2, self.y + self.height),  # 底部中点
                    (self.x + self.width // 2 - 3, self.y + self.height + 5),  # 左下
                    (self.x + self.width // 2 + 3, self.y + self.height + 5)  # 右下
                ]
                flame_color = (255, 200, 100)  # 火焰色
                pygame.draw.polygon(screen, flame_color, flame_points)

                outer_flame_color = (255, 100, 0)
                outer_points = [
                    (self.x + self.width // 2, self.y + self.height + 2),
                    (self.x + self.width // 2 - 5, self.y + self.height + 7),
                    (self.x + self.width // 2 + 5, self.y + self.height + 7)
                ]
                pygame.draw.polygon(screen, outer_flame_color, outer_points, 1)
        else:
            # 回退到原来的颜色绘制逻辑
            # 根据伤害值调整子弹大小
            bullet_width = self.width + (self.damage - 1) * 1  # 每点伤害宽度增加1像素
            bullet_height = self.height + (self.damage - 1) * 2  # 每点伤害高度增加2像素

            # 绘制子弹主体
            pygame.draw.rect(screen, self.color,
                             (self.x - (bullet_width - self.width) // 2,  # 居中绘制
                              self.y,
                              bullet_width,
                              bullet_height))

            # 高伤害子弹添加特殊效果
            if self.damage >= 3:
                # 绘制子弹核心（更亮的中心）
                core_color = (min(255, self.color[0] + 50),
                              min(255, self.color[1] + 30),
                              self.color[2])
                core_width = max(1, bullet_width - 4)
                core_height = max(1, bullet_height - 6)
                pygame.draw.rect(screen, core_color,
                                 (self.x - (core_width - self.width) // 2,
                                  self.y + 3,
                                  core_width,
                                  core_height))

            # 超高伤害子弹添加火焰效果
            if self.damage >= 5:
                # 绘制火焰尾迹
                flame_points = [
                    (self.x + self.width // 2, self.y + bullet_height),  # 底部中点
                    (self.x + self.width // 2 - 3, self.y + bullet_height + 5),  # 左下
                    (self.x + self.width // 2 + 3, self.y + bullet_height + 5)  # 右下
                ]
                flame_color = (255, 200, 100)  # 火焰色
                pygame.draw.polygon(screen, flame_color, flame_points)

                # 绘制火焰外焰
                outer_flame_color = (255, 100, 0)
                outer_points = [
                    (self.x + self.width // 2, self.y + bullet_height + 2),
                    (self.x + self.width // 2 - 5, self.y + bullet_height + 7),
                    (self.x + self.width // 2 + 5, self.y + bullet_height + 7)
                ]
                pygame.draw.polygon(screen, outer_flame_color, outer_points, 1)  # 只绘制边框

            # 高伤害子弹摆动效果（保持不变）
            if self.damage >= 4:
                # 根据y坐标产生正弦摆动
                swing = math.sin(self.y * 0.1) * 0.5
                self.x += swing

    def update(self):

        self.y += self.speed

        # 高伤害子弹可能有轻微左右摆动（增加难度）
        if self.damage >= 4:
            # 根据y坐标产生正弦摆动
            swing = math.sin(self.y * 0.1) * 0.5
            self.x += swing

    def get_rect(self):
        # 碰撞区域随伤害值增大而增大
        bullet_width = self.width + (self.damage - 1) * 1
        bullet_height = self.height + (self.damage - 1) * 2
        offset_x = (bullet_width - self.width) // 2

        return pygame.Rect(self.x - offset_x, self.y, bullet_width, bullet_height)

    def get_damage(self):
        """获取子弹伤害值"""
        return self.damage


# Boss子弹类
# 在 BossBullet.__init__() 中添加：
class BossBullet:
    def __init__(self, x, y, direction=(0, 1), boss_level=1, game_resources=None):
        self.game_resources = game_resources
        self.x = x
        self.y = y
        self.direction = direction
        self.boss_level = boss_level

        if direction[0] != 0:
            self.width = 12
            self.height = 6
        else:
            self.width = 6
            self.height = 12

        self.speed = 5 + (boss_level - 1) * 0.5
        self.original_speed = self.speed  # 添加：保存原始速度
        self.damage = 2 + (boss_level - 1) * 1

        # 根据伤害和方向设置颜色
        if direction[0] != 0:  # 水平子弹-紫色
            self.color = PURPLE
        elif direction[0] == 0 and direction[1] == 1:  # 垂直向下-红色
            self.color = (255, 100, 100)
        else:  # 斜向子弹-橙色
            self.color = ORANGE

        # 使用游戏资源中的图像
        if game_resources and hasattr(game_resources, 'images'):
            if 'boss_bullet' in game_resources.images:
                self.image = game_resources.images['boss_bullet']
            elif 'enemy_bullet' in game_resources.images:
                self.image = game_resources.images['enemy_bullet']
            else:
                self.image = None
        else:
            self.image = None

    def draw(self):
        if self.image:
            # 根据方向旋转图像
            angle = 0
            if self.direction[0] < 0:  # 向左
                angle = 90
            elif self.direction[0] > 0:  # 向右
                angle = -90
            elif self.direction[1] > 0:  # 向下（默认）
                angle = 180

            rotated_image = pygame.transform.rotate(self.image, angle)
            rect = rotated_image.get_rect(center=(self.x + self.width // 2,
                                                  self.y + self.height // 2))
            screen.blit(rotated_image, rect.topleft)
        else:
            # 绘制子弹
            pygame.draw.rect(screen, self.color,
                             (self.x, self.y, self.width, self.height))

            # 添加子弹核心（更亮的中心）
            core_width = max(1, self.width - 2)
            core_height = max(1, self.height - 2)
            core_color = (min(255, self.color[0] + 50),
                          min(255, self.color[1] + 50),
                          min(255, self.color[2] + 50))
            pygame.draw.rect(screen, core_color,
                             (self.x + 1, self.y + 1, core_width, core_height))

            # 高等级Boss子弹添加特效
            if self.boss_level >= 3:
                # 发光效果
                glow_color = (255, 200, 100, 100)
                glow_surface = pygame.Surface((self.width + 4, self.height + 4), pygame.SRCALPHA)
                pygame.draw.rect(glow_surface, glow_color,
                                 (0, 0, glow_surface.get_width(), glow_surface.get_height()))
                screen.blit(glow_surface, (self.x - 2, self.y - 2),
                            special_flags=pygame.BLEND_ALPHA_SDL2)

    def update(self):
        # 按方向移动
        self.x += self.speed * self.direction[0]
        self.y += self.speed * self.direction[1]

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def is_out_of_screen(self):
        """检查子弹是否超出屏幕"""
        return (self.y > HEIGHT or self.y + self.height < 0 or
                self.x > WIDTH or self.x + self.width < 0)
# 血包类
class HealthPack:
    def __init__(self, game_resources=None):
        self.game_resources = game_resources
        self.width = 30
        self.height = 30
        self.x = random.randint(0, WIDTH - self.width)
        self.y = random.randint(-100, -40)
        self.speed = random.uniform(1.0, 2.0)
        self.color = GREEN
        self.flash_timer = 0

        # 使用游戏资源中的图像
        if game_resources and hasattr(game_resources, 'images') and 'health_pack' in game_resources.images:
            self.image = game_resources.images['health_pack']
        else:
            self.image = None

    def draw(self):
        if self.image:
            # 闪烁效果
            self.flash_timer += 1
            if self.flash_timer % 10 < 5:
                screen.blit(self.image, (self.x, self.y))
            else:
                # 闪烁时变亮
                temp_image = self.image.copy()
                temp_image.fill((255, 255, 255, 128), special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(temp_image, (self.x, self.y))
        else:
            # 原来的绘制逻辑
            self.flash_timer += 1
            if self.flash_timer % 10 < 5:
                current_color = GREEN
            else:
                current_color = WHITE

            pygame.draw.rect(screen, current_color, (self.x + self.width // 2 - 5, self.y, 10, self.height))
            pygame.draw.rect(screen, current_color, (self.x, self.y + self.height // 2 - 5, self.width, 10))
            pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height), 2)

    def update(self):
        self.y += self.speed

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


# 子弹包类
class BulletPack:
    def __init__(self, game_resources=None):
        self.game_resources = game_resources
        self.width = 30
        self.height = 30
        self.x = random.randint(0, WIDTH - self.width)
        self.y = random.randint(-100, -40)
        self.speed = random.uniform(1.0, 1.5)
        self.color = PINK
        self.flash_timer = 0
        self.rotate_angle = 0

        # 使用游戏资源中的图像
        if game_resources and hasattr(game_resources, 'images') and 'bullet_pack' in game_resources.images:
            self.image = game_resources.images['bullet_pack']
        else:
            self.image = None

    def draw(self):
        if self.image:
            # 旋转和闪烁效果
            self.flash_timer += 1
            self.rotate_angle = (self.rotate_angle + 2) % 360

            if self.flash_timer % 10 < 5:
                # 正常显示
                rotated_image = pygame.transform.rotate(self.image, self.rotate_angle)
                rect = rotated_image.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
                screen.blit(rotated_image, rect.topleft)
            else:
                # 闪烁时变亮
                temp_image = self.image.copy()
                temp_image.fill((255, 255, 200, 128), special_flags=pygame.BLEND_RGBA_MULT)
                rotated_image = pygame.transform.rotate(temp_image, self.rotate_angle)
                rect = rotated_image.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
                screen.blit(rotated_image, rect.topleft)
        else:
            # 原来的绘制逻辑
            self.flash_timer += 1
            self.rotate_angle = (self.rotate_angle + 2) % 360

            if self.flash_timer % 10 < 5:
                current_color = PINK
            else:
                current_color = YELLOW

            center_x = self.x + self.width // 2
            center_y = self.y + self.height // 2
            radius = min(self.width, self.height) // 2 - 2
            angle_rad = math.radians(self.rotate_angle)

            points = []
            for i in range(3):
                angle = angle_rad + math.pi * 2 * i / 3
                px = center_x + radius * math.cos(angle)
                py = center_y + radius * math.sin(angle)
                points.append((px, py))

            pygame.draw.polygon(screen, current_color, points)
            pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height), 2)
            pygame.draw.rect(screen, WHITE, (center_x - 8, center_y - 2, 16, 4))
            pygame.draw.rect(screen, WHITE, (center_x - 2, center_y - 8, 4, 16))

    def update(self):
        self.y += self.speed

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


# 绘制登录界面
def draw_login_screen(user_manager, login_username, login_password,
                      active_login_user, active_login_pass, message=""):
    """绘制登录界面"""
    # 绘制背景
    screen.fill(DARK_BLUE)

    # 绘制星星
    for i in range(50):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        pygame.draw.circle(screen, WHITE, (x, y), 1)

    # 绘制标题
    title = FONTS["large"].render("我爱打飞机", True, LIGHT_BLUE)
    subtitle = FONTS["medium"].render("登录游戏", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
    screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 170))

    # 绘制用户名输入框
    user_rect = pygame.Rect(WIDTH // 2 - 150, 250, 300, 40)
    pygame.draw.rect(screen, WHITE, user_rect, 2)
    user_label = FONTS["normal"].render("用户名:", True, WHITE)
    screen.blit(user_label, (WIDTH // 2 - 200, 255))
    user_text = FONTS["normal"].render(login_username, True, WHITE)
    screen.blit(user_text, (WIDTH // 2 - 140, 260))

    # 绘制密码输入框
    pass_rect = pygame.Rect(WIDTH // 2 - 150, 310, 300, 40)
    pygame.draw.rect(screen, WHITE, pass_rect, 2)
    pass_label = FONTS["normal"].render("密码:", True, WHITE)
    screen.blit(pass_label, (WIDTH // 2 - 200, 315))
    pass_display = '*' * len(login_password)
    pass_text = FONTS["normal"].render(pass_display, True, WHITE)
    screen.blit(pass_text, (WIDTH // 2 - 140, 320))

    # 绘制登录按钮
    login_btn = pygame.Rect(WIDTH // 2 - 150, 380, 140, 45)
    pygame.draw.rect(screen, GREEN, login_btn)
    login_text = FONTS["normal"].render("登录", True, BLACK)
    screen.blit(login_text, (WIDTH // 2 - 150 + 70 - login_text.get_width() // 2, 390))

    # 绘制注册按钮
    register_btn = pygame.Rect(WIDTH // 2 + 10, 380, 140, 45)
    pygame.draw.rect(screen, BLUE, register_btn)
    register_text = FONTS["normal"].render("注册", True, WHITE)
    screen.blit(register_text, (WIDTH // 2 + 10 + 70 - register_text.get_width() // 2, 390))

    # 绘制游客按钮
    guest_btn = pygame.Rect(WIDTH // 2 - 100, 450, 200, 40)
    pygame.draw.rect(screen, ORANGE, guest_btn)
    guest_text = FONTS["normal"].render("游客模式", True, BLACK)
    screen.blit(guest_text, (WIDTH // 2 - guest_text.get_width() // 2, 460))

    # 绘制消息
    if message:
        msg_text = FONTS["normal"].render(message, True, RED if "失败" in message else GREEN)
        screen.blit(msg_text, (WIDTH // 2 - msg_text.get_width() // 2, 520))

    # 绘制当前登录用户（如果已登录）
    if user_manager.current_user:
        user_info = FONTS["small"].render(f"当前用户: {user_manager.current_user['username']}", True, GREEN)
        screen.blit(user_info, (10, 10))

        logout_btn = pygame.Rect(WIDTH - 120, 10, 110, 30)
        pygame.draw.rect(screen, RED, logout_btn)
        logout_text = FONTS["small"].render("退出登录", True, WHITE)
        screen.blit(logout_text, (WIDTH - 120 + 55 - logout_text.get_width() // 2, 15))

    # 绘制排行榜按钮
    leaderboard_btn = pygame.Rect(WIDTH - 150, HEIGHT - 50, 140, 40)
    pygame.draw.rect(screen, PURPLE, leaderboard_btn)
    leaderboard_text = FONTS["small"].render("查看排行榜", True, WHITE)
    screen.blit(leaderboard_text, (WIDTH - 150 + 70 - leaderboard_text.get_width() // 2, HEIGHT - 45))

    return user_rect, pass_rect, login_btn, register_btn, guest_btn, logout_btn if user_manager.current_user else None, leaderboard_btn


# 绘制注册界面
def draw_register_screen(register_username, register_password, register_email,
                         active_register_user, active_register_pass, active_register_email, message=""):
    """绘制注册界面"""
    # 绘制背景
    screen.fill(DARK_BLUE)

    # 绘制星星
    for i in range(50):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        pygame.draw.circle(screen, WHITE, (x, y), 1)

    # 绘制标题
    title = FONTS["large"].render("用户注册", True, LIGHT_BLUE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))

    # 绘制用户名输入框
    user_rect = pygame.Rect(WIDTH // 2 - 150, 150, 300, 40)
    pygame.draw.rect(screen, WHITE, user_rect, 2)
    user_label = FONTS["normal"].render("用户名:", True, WHITE)
    screen.blit(user_label, (WIDTH // 2 - 220, 155))
    user_text = FONTS["normal"].render(register_username, True, WHITE)
    screen.blit(user_text, (WIDTH // 2 - 140, 160))

    # 绘制密码输入框
    pass_rect = pygame.Rect(WIDTH // 2 - 150, 210, 300, 40)
    pygame.draw.rect(screen, WHITE, pass_rect, 2)
    pass_label = FONTS["normal"].render("密码:", True, WHITE)
    screen.blit(pass_label, (WIDTH // 2 - 220, 215))
    pass_display = '*' * len(register_password)
    pass_text = FONTS["normal"].render(pass_display, True, WHITE)
    screen.blit(pass_text, (WIDTH // 2 - 140, 220))

    # 绘制邮箱输入框
    email_rect = pygame.Rect(WIDTH // 2 - 150, 270, 300, 40)
    pygame.draw.rect(screen, WHITE, email_rect, 2)
    email_label = FONTS["normal"].render("邮箱:", True, WHITE)
    screen.blit(email_label, (WIDTH // 2 - 220, 275))
    email_text = FONTS["normal"].render(register_email, True, WHITE)
    screen.blit(email_text, (WIDTH // 2 - 140, 280))

    # 绘制注册按钮
    register_btn = pygame.Rect(WIDTH // 2 - 100, 340, 200, 45)
    pygame.draw.rect(screen, BLUE, register_btn)
    register_text = FONTS["normal"].render("注册", True, WHITE)
    screen.blit(register_text, (WIDTH // 2 - register_text.get_width() // 2, 350))

    # 绘制返回按钮
    back_btn = pygame.Rect(WIDTH // 2 - 100, 410, 200, 40)
    pygame.draw.rect(screen, ORANGE, back_btn)
    back_text = FONTS["normal"].render("返回登录", True, BLACK)
    screen.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, 420))

    # 绘制消息
    if message:
        msg_text = FONTS["normal"].render(message, True, RED if "失败" in message else GREEN)
        screen.blit(msg_text, (WIDTH // 2 - msg_text.get_width() // 2, 480))

    return user_rect, pass_rect, email_rect, register_btn, back_btn


# 绘制排行榜界面
def draw_leaderboard_screen(user_manager):
    """绘制排行榜界面"""
    # 绘制背景
    screen.fill(DARK_BLUE)

    # 绘制星星
    for i in range(50):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        pygame.draw.circle(screen, WHITE, (x, y), 1)

    # 绘制标题
    title = FONTS["large"].render("排行榜", True, YELLOW)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

    # 获取排行榜数据
    leaderboard = user_manager.get_leaderboard(10)

    # 绘制表头
    header_y = 120
    headers = ["排名", "用户名", "得分", "难度", "时间"]
    for i, header in enumerate(headers):
        header_text = FONTS["medium"].render(header, True, CYAN)
        screen.blit(header_text, (100 + i * 200, header_y))

    # 绘制分隔线
    pygame.draw.line(screen, WHITE, (50, header_y + 40), (WIDTH - 50, header_y + 40), 2)

    # 绘制排行榜数据
    data_y = header_y + 60
    for idx, record in enumerate(leaderboard):
        rank = idx + 1
        username, score, difficulty, game_time, date_played = record

        # 排名颜色
        if rank == 1:
            color = YELLOW
        elif rank == 2:
            color = LIGHT_BLUE
        elif rank == 3:
            color = ORANGE
        else:
            color = WHITE

        # 绘制数据
        rank_text = FONTS["normal"].render(str(rank), True, color)
        name_text = FONTS["normal"].render(username[:10], True, color)
        score_text = FONTS["normal"].render(str(score), True, color)
        diff_text = FONTS["normal"].render(str(difficulty), True, color)
        time_text = FONTS["normal"].render(f"{game_time}秒", True, color)

        screen.blit(rank_text, (120 - rank_text.get_width() // 2, data_y))
        screen.blit(name_text, (300 - name_text.get_width() // 2, data_y))
        screen.blit(score_text, (500 - score_text.get_width() // 2, data_y))
        screen.blit(diff_text, (700 - diff_text.get_width() // 2, data_y))
        screen.blit(time_text, (900 - time_text.get_width() // 2, data_y))

        data_y += 40

    # 绘制返回按钮
    back_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 100, 200, 50)
    pygame.draw.rect(screen, GREEN, back_btn)
    back_text = FONTS["normal"].render("返回", True, BLACK)
    screen.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, HEIGHT - 90))

    return back_btn


# 绘制用户统计界面
def draw_profile_screen(user_manager):
    """绘制用户统计界面"""
    if not user_manager.current_user:
        return None

    # 获取用户统计
    stats = user_manager.get_user_stats()
    if not stats:
        return None

    # 绘制背景
    screen.fill(DARK_BLUE)

    # 绘制星星
    for i in range(50):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        pygame.draw.circle(screen, WHITE, (x, y), 1)

    # 绘制标题
    title = FONTS["large"].render("用户统计", True, GREEN)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

    # 绘制用户名
    username_text = FONTS["medium"].render(f"用户名: {stats['username']}", True, WHITE)
    screen.blit(username_text, (WIDTH // 2 - username_text.get_width() // 2, 120))

    # 绘制统计数据
    stats_y = 180
    stat_items = [
        ("总游戏次数:", str(stats['total_games'])),
        ("总得分:", str(stats['total_score'])),
        ("最高分:", str(stats['highest_score'])),
        ("最高难度:", str(stats['highest_difficulty'])),
        ("总游戏时间:", f"{stats['total_game_time']}秒"),
    ]

    for label, value in stat_items:
        label_text = FONTS["normal"].render(label, True, CYAN)
        value_text = FONTS["normal"].render(value, True, WHITE)
        screen.blit(label_text, (WIDTH // 2 - 200, stats_y))
        screen.blit(value_text, (WIDTH // 2 + 100 - value_text.get_width() // 2, stats_y))
        stats_y += 50

    # 绘制最后游戏时间
    if stats['last_played']:
        last_played = FONTS["normal"].render(f"最后游戏: {stats['last_played']}", True, YELLOW)
        screen.blit(last_played, (WIDTH // 2 - last_played.get_width() // 2, stats_y + 30))

    # 绘制返回按钮
    back_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 100, 200, 50)
    pygame.draw.rect(screen, ORANGE, back_btn)
    back_text = FONTS["normal"].render("返回游戏", True, BLACK)
    screen.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, HEIGHT - 90))

    return back_btn


# 游戏主函数
def main():

    clock = pygame.time.Clock()

    # 初始化游戏资源管理器
    game_resources = GameResources()

    # 使用游戏资源管理器中的字体
    global FONTS
    FONTS = game_resources.fonts

    # 初始化用户管理器
    user_manager = UserManager()

    # 界面状态
    current_screen = "login"  # login, register, game, game_over, profile, leaderboard
    login_message = ""
    register_message = ""

    # 登录界面输入框
    login_username = ""
    login_password = ""
    active_login_user = False
    active_login_pass = False

    # 注册界面输入框
    register_username = ""
    register_password = ""
    register_email = ""
    active_register_user = False
    active_register_pass = False
    active_register_email = False

    # 游戏变量
    player = None
    enemies = []
    health_packs = []
    bullet_packs = []
    game_timer = 0
    base_enemy_spawn_interval = 60
    current_enemy_spawn_interval = base_enemy_spawn_interval
    min_enemy_spawn_interval = 30
    difficulty_level = 1
    elite_spawn_chance = 0.0
    tracking_spawn_chance = 0.0
    bullet_pack_timer = 0
    bullet_pack_interval = random.randint(3600, 7200)
    game_over = False
    # ========== BOSS相关变量 ==========
    boss = None  # 当前Boss
    boss_level = 1  # Boss等级（随击杀递增）
    boss_spawn_interval = 300  # 5分钟（300秒 * 60帧/秒 = 18000帧）
    last_boss_spawn_time = -boss_spawn_interval  # 确保开始时可以生成
    game_time_seconds = 0  # 游戏时间（秒）
    # ================================

    # 记录游戏结束时的数据
    final_score = 0
    final_game_time = 0
    final_difficulty = 0
    final_bullet_damage = 0
    final_enemies_killed = 0

    # 音频播放状态
    last_click_time = 0
    click_cooldown = 200  # 毫秒

    time_field_active_enemies = []  # 记录受时停领域影响的敌人

    while True:
        mouse_pos = pygame.mouse.get_pos()
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                user_manager.close()
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN :
                # 处理登录界面点击
                if current_screen == "login":
                    user_rect, pass_rect, login_btn, register_btn, guest_btn, logout_btn, leaderboard_btn = \
                        draw_login_screen(user_manager, login_username, login_password,
                                          active_login_user, active_login_pass, login_message)

                    if user_rect.collidepoint(mouse_pos):
                        active_login_user = True
                        active_login_pass = False
                        # 播放点击音效
                        if current_time - last_click_time > click_cooldown:
                            game_resources.play_sound('click')
                            last_click_time = current_time
                    elif pass_rect.collidepoint(mouse_pos):
                        active_login_user = False
                        active_login_pass = True
                        if current_time - last_click_time > click_cooldown:
                            game_resources.play_sound('click')
                            last_click_time = current_time
                    elif login_btn.collidepoint(mouse_pos):
                        if current_time - last_click_time > click_cooldown:
                            game_resources.play_sound('click')
                            last_click_time = current_time
                        if login_username and login_password:
                            success, message = user_manager.login(login_username, login_password)
                            login_message = message
                            if success:
                                current_screen = "game"
                                player = Player(game_resources)  # 传入资源管理器
                                game_over = False
                                game_timer = 0
                                difficulty_level = 1
                        else:
                            login_message = "请输入用户名和密码"
                    elif register_btn.collidepoint(mouse_pos):
                        if current_time - last_click_time > click_cooldown:
                            game_resources.play_sound('click')
                            last_click_time = current_time
                        current_screen = "register"
                        login_message = ""
                    elif guest_btn.collidepoint(mouse_pos):
                        if current_time - last_click_time > click_cooldown:
                            game_resources.play_sound('click')
                            last_click_time = current_time
                        current_screen = "game"
                        player = Player(game_resources)  # 传入资源管理器
                        game_over = False
                        game_timer = 0
                        difficulty_level = 1
                        login_message = ""
                    elif leaderboard_btn.collidepoint(mouse_pos):
                        if current_time - last_click_time > click_cooldown:
                            game_resources.play_sound('click')
                            last_click_time = current_time
                        current_screen = "leaderboard"
                        login_message = ""
                    elif logout_btn and logout_btn.collidepoint(mouse_pos):
                        if current_time - last_click_time > click_cooldown:
                            game_resources.play_sound('click')
                            last_click_time = current_time
                        user_manager.logout()
                        login_message = "已退出登录"
                    else:
                        active_login_user = False
                        active_login_pass = False

                # 处理注册界面点击
                elif current_screen == "register":
                    user_rect, pass_rect, email_rect, register_btn, back_btn = \
                        draw_register_screen(register_username, register_password, register_email,
                                             active_register_user, active_register_pass,
                                             active_register_email, register_message)

                    if user_rect.collidepoint(mouse_pos):
                        active_register_user = True
                        active_register_pass = False
                        active_register_email = False
                        if current_time - last_click_time > click_cooldown:
                            game_resources.play_sound('click')
                            last_click_time = current_time
                    elif pass_rect.collidepoint(mouse_pos):
                        active_register_user = False
                        active_register_pass = True
                        active_register_email = False
                        if current_time - last_click_time > click_cooldown:
                            game_resources.play_sound('click')
                            last_click_time = current_time
                    elif email_rect.collidepoint(mouse_pos):
                        active_register_user = False
                        active_register_pass = False
                        active_register_email = True
                        if current_time - last_click_time > click_cooldown:
                            game_resources.play_sound('click')
                            last_click_time = current_time
                    elif register_btn.collidepoint(mouse_pos):
                        if current_time - last_click_time > click_cooldown:
                            game_resources.play_sound('click')
                            last_click_time = current_time
                        if register_username and register_password:
                            success, message = user_manager.register(register_username, register_password,
                                                                     register_email)
                            register_message = message
                            if success:
                                register_username = ""
                                register_password = ""
                                register_email = ""
                                current_screen = "login"
                                login_message = "注册成功，请登录"
                        else:
                            register_message = "请输入用户名和密码"
                    elif back_btn.collidepoint(mouse_pos):
                        if current_time - last_click_time > click_cooldown:
                            game_resources.play_sound('click')
                            last_click_time = current_time
                        current_screen = "login"
                        register_message = ""
                    else:
                        active_register_user = False
                        active_register_pass = False
                        active_register_email = False

                # 处理排行榜界面点击
                elif current_screen == "leaderboard":
                    back_btn = draw_leaderboard_screen(user_manager)
                    if back_btn.collidepoint(mouse_pos):
                        if current_time - last_click_time > click_cooldown:
                            game_resources.play_sound('click')
                            last_click_time = current_time
                        current_screen = "login"

                # 处理用户统计界面点击
                elif current_screen == "profile":
                    back_btn = draw_profile_screen(user_manager)
                    if back_btn and back_btn.collidepoint(mouse_pos):
                        if current_time - last_click_time > click_cooldown:
                            game_resources.play_sound('click')
                            last_click_time = current_time
                        current_screen = "game"

                # 处理游戏结束界面点击
                elif current_screen == "game_over":
                    # 检查重新开始按钮
                    restart_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50)
                    if restart_btn.collidepoint(mouse_pos):
                        if current_time - last_click_time > click_cooldown:
                            game_resources.play_sound('click')
                            last_click_time = current_time
                        current_screen = "game"
                        player = Player(game_resources)  # 传入资源管理器
                        enemies = []
                        health_packs = []
                        bullet_packs = []
                        game_over = False
                        game_timer = 0
                        current_enemy_spawn_interval = base_enemy_spawn_interval
                        difficulty_level = 1
                        elite_spawn_chance = 0.0
                        tracking_spawn_chance = 0.0
                        bullet_pack_timer = 0
                        bullet_pack_interval = random.randint(3600, 7200)

                # 处理游戏中点击
                # 处理游戏中点击
                elif current_screen == "game" and not game_over:
                    if event.button == 1:  # 鼠标左键
                        # 如果技能准备好，使用技能
                        if player and player.skill_ready:
                            # 使用技能瞬移到鼠标位置
                            if player.use_skill1(mouse_pos[0], mouse_pos[1]):
                                # 技能使用成功
                                pass
                            else:
                                # 技能未准备好，这里可以播放提示音
                                if hasattr(game_resources, 'play_sound'):
                                    game_resources.play_sound('hit')
                    elif event.button == 3:  # 鼠标右键 - 春秋蝉技能 ← 新增
                            # 如果春秋蝉技能准备好，使用时光回溯
                        if player and hasattr(player, 'skill2_ready') and player.skill2_ready:
                            if player.use_skill2():
                                    # 技能使用成功
                                pass
                            else:
                                 # 技能未准备好或历史记录不足
                                if hasattr(game_resources, 'play_sound'):
                                    game_resources.play_sound('hit')
                        else:
                            # 技能未准备好，可以添加提示
                            pass

            if event.type == pygame.KEYDOWN:
                # 处理登录界面输入
                if current_screen == "login":
                    if active_login_user:
                        if event.key == pygame.K_BACKSPACE:
                            login_username = login_username[:-1]
                        elif event.key == pygame.K_RETURN:
                            active_login_user = False
                            active_login_pass = True
                        else:
                            login_username += event.unicode
                    elif active_login_pass:
                        if event.key == pygame.K_BACKSPACE:
                            login_password = login_password[:-1]
                        elif event.key == pygame.K_RETURN:
                            # 按回车键登录
                            if login_username and login_password:
                                success, message = user_manager.login(login_username, login_password)
                                login_message = message
                                if success:
                                    current_screen = "game"
                                    player = Player(game_resources)  # 传入资源管理器
                                    game_over = False
                                    game_timer = 0
                                    difficulty_level = 1
                        else:
                            login_password += event.unicode

                # 处理注册界面输入
                elif current_screen == "register":
                    if active_register_user:
                        if event.key == pygame.K_BACKSPACE:
                            register_username = register_username[:-1]
                        elif event.key == pygame.K_TAB:
                            active_register_user = False
                            active_register_pass = True
                        else:
                            register_username += event.unicode
                    elif active_register_pass:
                        if event.key == pygame.K_BACKSPACE:
                            register_password = register_password[:-1]
                        elif event.key == pygame.K_TAB:
                            active_register_pass = False
                            active_register_email = True
                        elif event.key == pygame.K_RETURN:
                            # 按回车键注册
                            if register_username and register_password:
                                success, message = user_manager.register(register_username, register_password,
                                                                         register_email)
                                register_message = message
                                if success:
                                    register_username = ""
                                    register_password = ""
                                    register_email = ""
                                    current_screen = "login"
                                    login_message = "注册成功，请登录"
                        else:
                            register_password += event.unicode
                    elif active_register_email:
                        if event.key == pygame.K_BACKSPACE:
                            register_email = register_email[:-1]
                        elif event.key == pygame.K_TAB:
                            active_register_email = False
                            active_register_user = True
                        elif event.key == pygame.K_RETURN:
                            # 按回车键注册
                            if register_username and register_password:
                                success, message = user_manager.register(register_username, register_password,
                                                                         register_email)
                                register_message = message
                                if success:
                                    register_username = ""
                                    register_password = ""
                                    register_email = ""
                                    current_screen = "login"
                                    login_message = "注册成功，请登录"
                        else:
                            register_email += event.unicode

                # 游戏中按ESC返回登录界面
                elif current_screen == "game" and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if player:  # 添加player检查
                            if boss in enemies:
                                enemies.remove(boss)

                            boss = None
                            boss_level = 1
                            last_boss_spawn_time = 0
                            game_over = True
                            player.level = 1
                            enemies = []
                            cleanup_time_field_effects(player)

                            current_screen = "login"

                    # 其他按键处理
                    # ... 现有按键处理 ...

                    # 空格键使用时停领域技能
                    elif event.key == pygame.K_SPACE and player:
                        if hasattr(player, 'use_time_field'):
                            player.use_time_field()


                # 游戏中按P查看个人统计
                elif current_screen == "game" and event.key == pygame.K_p and user_manager.current_user:
                    current_screen = "profile"

            # 游戏结束处理
            if current_screen == "game_over" and event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                current_screen = "login"

        # 根据当前屏幕状态更新和绘制
        if current_screen == "login":
            draw_login_screen(user_manager, login_username, login_password,
                              active_login_user, active_login_pass, login_message)

        elif current_screen == "register":
            draw_register_screen(register_username, register_password, register_email,
                                 active_register_user, active_register_pass,
                                 active_register_email, register_message)

        elif current_screen == "leaderboard":
            draw_leaderboard_screen(user_manager)

        elif current_screen == "profile":
            draw_profile_screen(user_manager)


        elif current_screen == "game":

            if not game_over and player:

                # 游戏计时
                game_timer += 1
                # ========== 更新游戏时间（秒） ==========
                # 假设游戏运行在60FPS，每帧增加1/60
                game_time_seconds += 1 / 60
                # ====================================
                # 随时间上升普通敌人生成速度由60一个逐渐升到30一个
                # 每30秒（1800帧）加速一次

                if game_timer % 1800 == 0 and game_timer > 0:

                    if current_enemy_spawn_interval > min_enemy_spawn_interval:
                        current_enemy_spawn_interval = max(min_enemy_spawn_interval,

                                                           current_enemy_spawn_interval - 2)

                # 每10秒增加难度

                if game_timer % 600 == 0:  # 600帧 = 10秒（60帧/秒）

                    difficulty_level += 1

                    # 增加精英敌机生成概率

                    elite_spawn_chance = min(0.35, elite_spawn_chance + 0.05)

                    # 增加追踪敌机生成概率（从第2级开始）

                    if difficulty_level >= 2:
                        tracking_spawn_chance = min(0.25, tracking_spawn_chance + 0.03)

                # 获取按键状态
                keys = pygame.key.get_pressed()
                # 移动玩家
                player.move(keys)
                # 更新玩家和子弹
                player.update()

                # ========== 检查是否需要生成Boss ==========

                # 当前游戏时间（分钟）


                game_seconds = int(game_timer // 60)  # 帧→秒

                game_minutes = int(game_seconds // 60)  # 秒→分钟

                # 每分钟生成一个Boss（从第1分钟开始）
                if (game_minutes >= 2 and  (game_minutes % 2 == 0) and# 单局游戏开始2分钟后（实际60秒后）
                        game_minutes > last_boss_spawn_time and  # 确保是新的一分钟
                        boss is None):  # 当前没有Boss
                    # 生成Boss
                    boss = Enemy(is_boss=True, boss_level=boss_level, game_resources=game_resources)
                    game_resources.play_sound('warn')
                    enemies.append(boss)  # 添加到敌人列表中统一管理
                    last_boss_spawn_time = game_minutes
                    print(f"🚀 Boss Level {boss_level} 出现！")

                # =========================================
                # 生成敌机
                if game_timer % current_enemy_spawn_interval == 0:
                    # 如果有Boss存在，减少普通敌人生成概率

                    if boss:

                        # 只在50%的概率下生成普通敌人

                        if random.random() < 0.5:

                            rand_val = random.random()

                            if rand_val < tracking_spawn_chance and difficulty_level >= 2:

                                # 生成追踪敌机

                                enemies.append(TrackingEnemy(difficulty_level, game_resources))

                            elif rand_val < tracking_spawn_chance + elite_spawn_chance and difficulty_level >= 2:

                                # 生成精英敌机

                                enemies.append(EliteEnemy(difficulty_level, game_resources))

                            else:

                                # 生成普通敌机

                                enemies.append(Enemy(difficulty_level, game_resources))

                    else:

                        # 正常生成敌人

                        rand_val = random.random()

                        if rand_val < tracking_spawn_chance and difficulty_level >= 2:

                            # 生成追踪敌机

                            enemies.append(TrackingEnemy(difficulty_level, game_resources))

                        elif rand_val < tracking_spawn_chance + elite_spawn_chance and difficulty_level >= 2:

                            # 生成精英敌机

                            enemies.append(EliteEnemy(difficulty_level, game_resources))

                        else:

                            # 生成普通敌机

                            enemies.append(Enemy(difficulty_level, game_resources))

                # 更新敌机

                # 更新敌机
                for enemy in enemies[:]:
                    # 所有敌机都只需要调用 enemy.update()，因为：
                    # 1. 普通 Enemy 类有 update() 方法
                    # 2. TrackingEnemy 和 EliteEnemy 继承了 Enemy 的 update() DDDDD
                    # 3. Boss 是 Enemy(is_boss=True) 创建的，也有 update() 方法
                    # ========== 特殊处理Boss的边界检查 ==========
                    # Boss不出界，普通敌人出界则移除
                    # ========== 让Boss开火 ==========
                    if hasattr(enemy, 'is_boss') and enemy.is_boss:
                        if enemy.can_fire():
                            enemy.fire()

                    if not hasattr(enemy, 'is_boss') or not enemy.is_boss:
                        # 普通敌人：检查是否出界
                        if enemy.is_out_of_screen():
                            enemies.remove(enemy)
                    # ============================================

                # 生成血包（概率生成）
                if game_timer % 300 == 0 and random.random() < 0.3:  # 每5秒有30%概率生成血包
                    health_packs.append(HealthPack(game_resources))

                # 生成子弹包（随机生成）
                bullet_pack_timer += 1
                if bullet_pack_timer >= bullet_pack_interval:
                    bullet_packs.append(BulletPack(game_resources))
                    bullet_pack_timer = 0
                    bullet_pack_interval = random.randint(3600, 4600)  # 重新设置间隔

                # 更新敌机
                for enemy in enemies[:]:


                    should_remove_enemy = False  # 标记是否需要移除敌机

                    # 更新不同类型的敌机
                    if isinstance(enemy, TrackingEnemy):
                        # 追踪敌机的update方法返回是否需要移除
                        should_remove_enemy = enemy.update(player.x + player.width // 2,
                                                           player.y + player.height // 2,
                                                           game_timer)
                    else:
                        enemy.update()

                    # 如果追踪敌机生命周期结束，立即移除并跳过后续检查
                    if should_remove_enemy:
                        enemies.remove(enemy)
                        continue

                    # 检查敌机是否与玩家碰撞
                    if player.get_rect().colliderect(enemy.get_rect()):
                        # 计算伤害
                        if hasattr(enemy, 'is_boss') and enemy.is_boss:
                            # Boss碰撞伤害更高
                            damage_amount = enemy.damage * 2
                        else:
                            # 普通敌人伤害
                            damage_amount = enemy.damage if hasattr(enemy, 'damage') else 1

                        # 玩家受到伤害
                        player.health -= damage_amount

                        # 移除敌机（Boss不因碰撞而移除，只造成伤害）
                        if not (hasattr(enemy, 'is_boss') and enemy.is_boss):
                            if enemy in enemies:
                                enemies.remove(enemy)

                        # 播放击中音效
                        game_resources.play_sound('hit')

                        if player.health <= 0:
                            game_over = True
                            final_score = player.score
                            final_game_time = game_timer // 60
                            final_difficulty = difficulty_level
                            final_bullet_damage = player.bullet_damage
                            final_enemies_killed = player.enemies_killed
                            current_screen = "game_over"
                            boss = None
                            boss_level =1
                            last_boss_spawn_time = 0
                            player.level = 1
                            cleanup_time_field_effects(player)
                            # 播放游戏结束音效
                            game_resources.play_sound('game_over')

                            # 保存分数到数据库
                            if user_manager.current_user:
                                user_manager.save_score(final_score, final_difficulty,
                                                        final_game_time, final_bullet_damage,
                                                        final_enemies_killed)

                        if not (hasattr(enemy, 'is_boss') and enemy.is_boss):
                            continue  # 普通敌机已移除，跳过后续检查

                    # 检查敌机是否飞出屏幕
                    if enemy.y > HEIGHT:
                        enemies.remove(enemy)
                        continue  # 敌机已移除，跳过后续检查
                        # ========== 应用时停领域效果 ==========
                    # ========== 应用时停领域效果 ==========
                    # ========== 应用时停领域效果 ==========
                    if player and hasattr(player, 'time_field_active') and player.time_field_active:
                        # 1. 检查敌机是否在领域内
                        enemy_center_x = enemy.x + enemy.width // 2
                        enemy_center_y = enemy.y + enemy.height // 2

                        enemy_in_field = player.is_in_time_field(enemy_center_x, enemy_center_y)

                        if enemy_in_field:
                            # 标记敌人受时停影响
                            if enemy not in player._time_field_affected_enemies:
                                player._time_field_affected_enemies.append(enemy)

                            # 减慢敌人移动速度
                            if not enemy.is_slowed:
                                enemy.original_speed = enemy.speed
                                enemy.speed = enemy.speed * player.time_field_bullet_slow
                                enemy.is_slowed = True

                        # 2. 检查该敌机的所有子弹是否在领域内（重要！）
                        if hasattr(enemy, 'bullets'):
                            for bullet in enemy.bullets:
                                # 计算子弹中心位置
                                if hasattr(bullet, 'get_center'):
                                    bullet_center = bullet.get_center()
                                else:
                                    bullet_center_x = bullet.x + bullet.width // 2
                                    bullet_center_y = bullet.y + bullet.height // 2

                                # 检查子弹是否在领域内
                                bullet_in_field = player.is_in_time_field(bullet_center_x, bullet_center_y)

                                if bullet_in_field:
                                    # 标记子弹受时停影响
                                    if not hasattr(bullet, 'is_slowed'):
                                        bullet.is_slowed = True
                                        if not hasattr(bullet, 'original_speed'):
                                            bullet.original_speed = bullet.speed
                                        bullet.speed = bullet.original_speed * player.time_field_bullet_slow
                                else:
                                    # 子弹不在领域内，恢复速度
                                    if hasattr(bullet, 'is_slowed') and bullet.is_slowed:
                                        bullet.speed = bullet.original_speed
                                        bullet.is_slowed = False
                    else:
                        # 时停领域未激活时，恢复所有受影响的子弹
                        if hasattr(enemy, 'bullets'):
                            for bullet in enemy.bullets:
                                if hasattr(bullet, 'is_slowed') and bullet.is_slowed:
                                    bullet.speed = bullet.original_speed
                                    bullet.is_slowed = False
                    # ====================================

                    # 检查玩家子弹是否击中敌机
                    for bullet in player.bullets[:]:
                        for enemy in enemies[:]:  # 遍历所有敌人（包括普通敌人和Boss）
                            if bullet.get_rect().colliderect(enemy.get_rect()):
                                # 不同类型的敌机有不同的血量
                                if hasattr(enemy, 'health'):
                                    enemy.health -= bullet.damage

                                    # 播放击中音效
                                    game_resources.play_sound('hit')

                                    # 检查是否被击败
                                    if enemy.health <= 0:
                                        # ========== 普通敌机和Boss共用击败逻辑 ==========
                                        if hasattr(enemy, 'is_boss') and enemy.is_boss:
                                            # BOSS被击败
                                            player.score += enemy.get_score()  # 使用get_score方法

                                            # Boss特殊奖励
                                            player.boss_killed += 1  # 记录击杀Boss数量
                                            player.score += 5000  # Boss额外奖励
                                            boss = None
                                            boss_level +=1
                                            player.level += 1


                                            print(f"🎉 Boss Level {enemy.boss_level} 被击败！")

                                        elif isinstance(enemy, EliteEnemy):
                                            player.score += 50
                                        elif isinstance(enemy, TrackingEnemy):
                                            player.score += 80  # 追踪敌机得分更高
                                        else:
                                            player.score += 10

                                        player.enemies_killed += 1
                                        enemies.remove(enemy)

                                        # 播放爆炸音效
                                        game_resources.play_sound('explosion')

                                    else:
                                        # ========== Boss受伤但未被击败的特殊效果 ==========
                                        if hasattr(enemy, 'is_boss') and enemy.is_boss:
                                            # Boss受伤闪烁效果
                                            enemy.flashing = True
                                            enemy.flash_timer = 10

                                            # Boss低血量警告
                                            if enemy.health < enemy.max_health * 0.3:
                                                # 播放低血量警告音效
                                                game_resources.play_sound('hit')

                                else:
                                    # 没有血量属性的敌人（旧代码兼容）
                                    player.score += 10
                                    player.enemies_killed += 1
                                    enemies.remove(enemy)
                                    game_resources.play_sound('explosion')


                                # 移除子弹
                                if bullet in player.bullets:
                                    player.bullets.remove(bullet)
                                break  # 一颗子弹只能击中一个敌机



                        # ========== 检查Boss子弹是否击中玩家 ==========

                        for enemy in enemies[:]:
                            if hasattr(enemy, 'is_boss') and enemy.is_boss and hasattr(enemy, 'bullets'):
                                for boss_bullet in enemy.bullets[:]:
                                    # 现在boss_bullet可能是BossBullet对象或字典
                                    if hasattr(boss_bullet, 'get_rect'):
                                        # BossBullet对象
                                        bullet_rect = boss_bullet.get_rect()
                                        damage = boss_bullet.damage
                                    else:
                                        # 旧的字典格式
                                        bullet_rect = pygame.Rect(
                                            boss_bullet['x'], boss_bullet['y'],
                                            boss_bullet['width'], boss_bullet['height']
                                        )
                                        damage = boss_bullet.get('damage', enemy.damage)

                                    if bullet_rect.colliderect(player.get_rect()):
                                        # 玩家受到伤害
                                        player.health -= damage

                                        # 移除子弹
                                        enemy.bullets.remove(boss_bullet)

                                        # 播放击中音效
                                        game_resources.play_sound('hit')

                                        if player.health <= 0:
                                            game_over = True
                                            cleanup_time_field_effects(player)
                                            final_score = player.score
                                            final_game_time = game_timer // 60
                                            final_difficulty = difficulty_level
                                            final_bullet_damage = player.bullet_damage
                                            final_enemies_killed = player.enemies_killed
                                            current_screen = "game_over"
                                            boss = None
                                            boss_level = 1
                                            last_boss_spawn_time = 0
                                            player.level = 1
                                            # 播放游戏结束音效
                                            game_resources.play_sound('game_over')

                                            # 保存分数到数据库
                                            if user_manager.current_user:
                                                user_manager.save_score(final_score, final_difficulty,
                                                                        final_game_time, final_bullet_damage,
                                                                        final_enemies_killed)
                                        break  # 一颗子弹只检查一次
                        # ============================================

                        # 检查精英敌机的子弹是否击中玩家
                        # 检查精英敌机的子弹是否击中玩家
                        if isinstance(enemy, EliteEnemy) and hasattr(enemy, 'bullets'):
                            for bullet in enemy.bullets[:]:
                                if bullet.get_rect().colliderect(player.get_rect()):
                                    # 获取子弹伤害
                                    bullet_damage = 1  # 默认
                                    if hasattr(bullet, 'damage'):
                                        bullet_damage = bullet.damage

                                    # 应用伤害
                                    player.health -= bullet_damage

                                    # 移除子弹
                                    enemy.bullets.remove(bullet)

                                    # 播放击中音效
                                    game_resources.play_sound('hit')

                                    # 检查玩家是否死亡
                                    if player.health <= 0:
                                        game_over = True
                                        cleanup_time_field_effects(player)
                                        final_score = player.score
                                        final_game_time = game_timer // 60
                                        final_difficulty = difficulty_level
                                        final_bullet_damage = player.bullet_damage
                                        final_enemies_killed = player.enemies_killed
                                        current_screen = "game_over"
                                        game_resources.play_sound('game_over')
                                        boss = None
                                        boss_level = 1
                                        last_boss_spawn_time = 0
                                        player.level = 1

                                        if user_manager.current_user:
                                            user_manager.save_score(final_score, final_difficulty,
                                                                    final_game_time, final_bullet_damage,
                                                                    final_enemies_killed)
                                    break
                # 更新血包
                for health_pack in health_packs[:]:
                    health_pack.update()

                    # 检查血包是否与玩家碰撞
                    if player.get_rect().colliderect(health_pack.get_rect()):
                        if player.health < player.max_health:
                            player.health += 1
                            # 播放获得道具音效
                            game_resources.play_sound('powerup')
                        health_packs.remove(health_pack)

                    # 检查血包是否飞出屏幕
                    if health_pack.y > HEIGHT:
                        health_packs.remove(health_pack)

                # 更新子弹包
                for bullet_pack in bullet_packs[:]:
                    bullet_pack.update()

                    # 检查子弹包是否与玩家碰撞a
                    if player.get_rect().colliderect(bullet_pack.get_rect()):
                        player.increase_bullet_damage()
                        bullet_packs.remove(bullet_pack)
                        # 播放获得道具音效
                        game_resources.play_sound('powerup')

                    # 检查子弹包是否飞出屏幕
                    if bullet_pack.y > HEIGHT:
                        bullet_packs.remove(bullet_pack)

            # 绘制科幻风格渐变背景
            # 从上到下的渐变：深蓝→紫色→暗紫
            for y in range(0, HEIGHT, 2):
                # 计算当前行的颜色
                progress = y / HEIGHT

                # 渐变颜色：深蓝(0, 0, 40) → 暗紫(30, 0, 60) → 深紫(20, 0, 40)
                if progress < 0.3:
                    # 顶部：深蓝色
                    color_r = int(0 + progress * 100)
                    color_g = int(0 + progress * 30)
                    color_b = int(40 + progress * 70)
                elif progress < 0.7:
                    # 中部：紫色过渡
                    sub_progress = (progress - 0.3) / 0.4
                    color_r = int(30 + sub_progress * 10)
                    color_g = int(10 + sub_progress * 5)
                    color_b = int(60 - sub_progress * 20)
                else:
                    # 底部：深紫色
                    sub_progress = (progress - 0.7) / 0.3
                    color_r = int(40 - sub_progress * 20)
                    color_g = int(15 - sub_progress * 15)
                    color_b = int(40 - sub_progress * 10)

                pygame.draw.line(screen, (color_r, color_g, color_b),
                                 (0, y), (WIDTH, y), 2)

            # 绘制多层次星云效果
            # 第一层：稀疏的亮星（白色/淡蓝色）
            for i in range(30):
                x = random.randint(0, WIDTH)
                y = random.randint(0, HEIGHT)
                size = random.uniform(0.8, 1.5)
                brightness = random.randint(200, 255)
                # 随机颜色：白色或淡蓝色
                if random.random() > 0.7:
                    star_color = (brightness, brightness, brightness)  # 白色
                else:
                    star_color = (brightness - 50, brightness - 30, brightness)  # 淡蓝色

                # 绘制主星
                pygame.draw.circle(screen, star_color, (int(x), int(y)), size)

                # 添加微弱的发光效果
                glow_size = size + random.uniform(0.5, 1.5)
                glow_alpha = random.randint(30, 60)
                glow_surface = pygame.Surface((int(glow_size * 4), int(glow_size * 4)), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (*star_color, glow_alpha),
                                   (int(glow_size * 2), int(glow_size * 2)), glow_size)
                screen.blit(glow_surface, (int(x - glow_size * 2), int(y - glow_size * 2)))

            # 第二层：中等密度的闪烁星（蓝色/紫色）
            current_time = pygame.time.get_ticks()
            for i in range(40):
                x = random.randint(0, WIDTH)
                y = random.randint(0, HEIGHT)
                base_size = random.uniform(0.5, 1.2)

                # 创建闪烁效果
                blink = (math.sin(current_time * 0.002 + i * 0.5) + 1) * 0.5
                size = base_size * (0.8 + blink * 0.4)
                brightness = int(150 + blink * 105)

                # 随机颜色：蓝色系
                if random.random() > 0.5:
                    star_color = (brightness - 100, brightness - 50, brightness)  # 蓝色
                else:
                    star_color = (brightness - 50, brightness - 100, brightness)  # 紫色

                pygame.draw.circle(screen, star_color, (int(x), int(y)), size)

            # 第三层：密集的暗星（作为背景）
            for i in range(80):
                x = random.randint(0, WIDTH)
                y = random.randint(0, HEIGHT)
                size = random.uniform(0.3, 0.8)
                brightness = random.randint(80, 120)

                # 暗蓝色/暗紫色
                if random.random() > 0.5:
                    star_color = (brightness - 60, brightness - 40, brightness)  # 暗蓝
                else:
                    star_color = (brightness - 40, brightness - 60, brightness)  # 暗紫

                pygame.draw.circle(screen, star_color, (int(x), int(y)), size)

            # 绘制星云光晕效果（随机位置的柔和光晕）
            for i in range(4):
                nebula_x = WIDTH * (0.2 + i * 0.2)
                nebula_y = HEIGHT * random.uniform(0.3, 0.7)
                nebula_radius = random.randint(80, 150)

                # 创建多层光晕
                for layer in range(3):
                    radius = nebula_radius * (0.5 + layer * 0.5)
                    alpha = 20 - layer * 8

                    # 随机光晕颜色（蓝紫色系）
                    if i % 2 == 0:
                        nebula_color = (50, 30, 100, alpha)  # 蓝紫色
                    else:
                        nebula_color = (70, 20, 80, alpha)  # 紫红色

                    nebula_surface = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
                    pygame.draw.circle(nebula_surface, nebula_color,
                                       (int(radius), int(radius)), int(radius))
                    screen.blit(nebula_surface, (int(nebula_x - radius), int(nebula_y - radius)))

            # 添加微弱的网格线效果（科幻感）
            grid_alpha = 15
            grid_spacing = 40
            grid_color = (100, 120, 200, grid_alpha)

            # 垂直网格线
            for x in range(0, WIDTH, grid_spacing):
                grid_surface = pygame.Surface((2, HEIGHT), pygame.SRCALPHA)
                grid_surface.fill(grid_color)
                screen.blit(grid_surface, (x, 0))

            # 水平网格线
            for y in range(0, HEIGHT, grid_spacing):
                grid_surface = pygame.Surface((WIDTH, 2), pygame.SRCALPHA)
                grid_surface.fill(grid_color)
                screen.blit(grid_surface, (0, y))

            # 添加屏幕边缘的光晕效果
            edge_glow_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            # 顶部光晕
            for y in range(20):
                alpha = int(30 * (1 - y / 20))
                pygame.draw.line(edge_glow_surface, (100, 150, 255, alpha),
                                 (0, y), (WIDTH, y), 1)
            # 底部光晕
            for y in range(HEIGHT - 20, HEIGHT):
                alpha = int(30 * ((y - (HEIGHT - 20)) / 20))
                pygame.draw.line(edge_glow_surface, (100, 150, 255, alpha),
                                 (0, y), (WIDTH, y), 1)
            screen.blit(edge_glow_surface, (0, 0))

            # 绘制玩家子弹
            for bullet in player.bullets:
                bullet.draw()

            # 绘制敌机
            for enemy in enemies:
                enemy.draw()
                # 绘制精英敌机的子弹
                if isinstance(enemy, EliteEnemy):
                    for bullet in enemy.bullets:
                        bullet.draw()

            # 绘制血包
            for health_pack in health_packs:
                health_pack.draw()

            # 绘制子弹包
            for bullet_pack in bullet_packs:
                bullet_pack.draw()

            # 绘制玩家
            player.draw()

            # 显示难度等级和游戏时间
            time_seconds = game_timer // 60
            info = FONTS["small"].render(
                f"难度：{difficulty_level}  时间：{time_seconds // 60:02d}:{time_seconds % 60:02d}", True, WHITE
            )
            screen.blit(info, (10, HEIGHT - 90))

            # 显示敌机生成速度
            spawn_text = FONTS["small"].render(f"敌机生成：{60 / current_enemy_spawn_interval:.1f}/秒", True, WHITE)
            screen.blit(spawn_text, (10, HEIGHT - 60))

            # 显示特殊敌机概率
            special_text = FONTS["small"].render(
                f"精英：{elite_spawn_chance * 100:.0f}%  追踪：{tracking_spawn_chance * 100:.0f}%", True, WHITE)
            screen.blit(special_text, (10, HEIGHT - 30))

            # ========== 显示双技能条（右下角） ==========
            if player:
                # 技能条基本参数
                bar_width = 140
                bar_height = 12
                bar_spacing = 35  # 两个技能条之间的间距
                bar_offset = 15  # 技能条之间的垂直偏移

                # 技能1（定仙游）- 上技能条
                bar1_x = WIDTH - 150
                bar1_y = 280  # 在子弹伤害信息下方

                # 技能2（春秋蝉）- 中技能条
                bar2_x = WIDTH - 150
                bar2_y = bar1_y + bar_height + bar_spacing  # 在技能1下方

                # 技能3（时停领域）- 下技能条
                bar3_x = WIDTH - 150
                bar3_y = bar2_y + bar_height + bar_spacing  # 在技能2下方

                # ===== 绘制技能1（定仙游）条 =====
                if hasattr(player, 'skill_charge'):  # 检查是否有技能1属性
                    # 背景
                    pygame.draw.rect(screen, (40, 40, 40), (bar1_x, bar1_y, bar_width, bar_height))

                    # 充能条
                    fill1_width = int(bar_width * (player.skill_charge / 100))

                    # 颜色根据状态变化
                    if player.skill_ready:
                        bar1_color = (0, 200, 255)  # 蓝色
                        # 闪烁效果
                        if pygame.time.get_ticks() % 800 < 400:
                            bar1_color = (100, 230, 255)
                    elif player.skill_charge > 50:
                        bar1_color = (0, 255, 100)  # 绿色
                    else:
                        bar1_color = (255, 100, 0)  # 橙色

                    pygame.draw.rect(screen, bar1_color, (bar1_x, bar1_y, fill1_width, bar_height))

                    # 边框
                    pygame.draw.rect(screen, (200, 200, 200), (bar1_x, bar1_y, bar_width, bar_height), 1)

                    # 技能文本
                    if player.skill_ready:
                        skill1_text = FONTS["small"].render("定仙游(左键)", True, bar1_color)
                    else:
                        cooldown_seconds = max(0, player.skill_cooldown // 60)
                        skill1_text = FONTS["small"].render(f"定仙游({cooldown_seconds}s)", True, (180, 180, 180))

                    screen.blit(skill1_text, (bar1_x, bar1_y + bar_height + 2))

                # ===== 绘制技能2（春秋蝉）条 =====
                if hasattr(player, 'skill2_charge'):  # 检查是否有技能2属性
                    # 背景
                    pygame.draw.rect(screen, (40, 40, 40), (bar2_x, bar2_y, bar_width, bar_height))

                    # 充能条
                    fill2_width = int(bar_width * (player.skill2_charge / 100))

                    # 颜色根据状态变化（使用不同的颜色主题）
                    if player.skill2_ready:
                        bar2_color = (100, 255, 100)  # 绿色（时光主题）
                        # 闪烁效果
                        if pygame.time.get_ticks() % 800 < 400:
                            bar2_color = (150, 255, 150)
                    elif player.skill2_charge > 50:
                        bar2_color = (255, 200, 0)  # 金色
                    else:
                        bar2_color = (255, 100, 100)  # 红色

                    pygame.draw.rect(screen, bar2_color, (bar2_x, bar2_y, fill2_width, bar_height))

                    # 边框
                    pygame.draw.rect(screen, (200, 200, 200), (bar2_x, bar2_y, bar_width, bar_height), 1)

                    # 技能文本
                    if player.skill2_ready:
                        skill2_text = FONTS["small"].render("春秋蝉(右键)", True, bar2_color)
                    else:
                        cooldown_seconds = max(0, player.skill2_cooldown // 60)
                        skill2_text = FONTS["small"].render(f"春秋蝉({cooldown_seconds}s)", True, (180, 180, 180))

                    screen.blit(skill2_text, (bar2_x, bar2_y + bar_height + 2))

                    # 显示技能2额外信息（可选）
                    if hasattr(player, 'position_history'):
                        history_seconds = len(player.position_history) // 60
                        if history_seconds < 2:  # 历史记录不足2秒
                            hint_text = FONTS["small"].render(f"({history_seconds}s/2s)", True, (255, 150, 0))
                            screen.blit(hint_text, (bar2_x + bar_width + 5, bar2_y))

                # ===== 绘制技能3（时停领域）条 =====
                if hasattr(player, 'time_field_charge'):  # 检查是否有技能3属性
                    # 背景
                    pygame.draw.rect(screen, (40, 40, 40), (bar3_x, bar3_y, bar_width, bar_height))

                    # 充能条
                    fill3_width = int(bar_width * (player.time_field_charge / 100))

                    # 颜色根据状态变化（使用蓝色系，表示时间控制）
                    if player.time_field_ready:
                        bar3_color = (100, 150, 255)  # 亮蓝色
                        # 闪烁效果（与技能1、2不同的频率）
                        if pygame.time.get_ticks() % 600 < 300:
                            bar3_color = (150, 180, 255)
                    elif player.time_field_charge > 50:
                        bar3_color = (80, 120, 220)  # 中等蓝色
                    else:
                        bar3_color = (60, 90, 180)  # 深蓝色

                    pygame.draw.rect(screen, bar3_color, (bar3_x, bar3_y, fill3_width, bar_height))

                    # 边框
                    pygame.draw.rect(screen, (200, 200, 200), (bar3_x, bar3_y, bar_width, bar_height), 1)

                    # 技能文本
                    if player.time_field_ready:
                        skill3_text = FONTS["small"].render("时停领域(空格)", True, bar3_color)
                    else:
                        cooldown_seconds = max(0, player.time_field_cooldown // 60)
                        skill3_text = FONTS["small"].render(f"时停领域({cooldown_seconds}s)", True, (180, 180, 180))

                    screen.blit(skill3_text, (bar3_x, bar3_y + bar_height + 2))

                    # 如果时停领域正在激活中，显示持续时间
                    if hasattr(player, 'time_field_active') and player.time_field_active:
                        remaining_time = max(0, (player.time_field_duration - player.time_field_use_time) // 60)
                        duration_text = FONTS["small"].render(f"持续:{remaining_time}s", True, (100, 200, 255))
                        screen.blit(duration_text, (bar3_x + bar_width + 5, bar3_y))

                # ===== 绘制技能标题（可选）=====
                # 在技能条上方添加标题
                skills_title = FONTS["small"].render("技能状态", True, (200, 200, 200))
                screen.blit(skills_title, (bar1_x, bar1_y - 30))

                # 绘制分隔线（视觉区分）
                pygame.draw.line(screen, (100, 100, 100),
                                 (bar1_x, bar1_y - 5),
                                 (bar1_x + bar_width, bar1_y - 5), 1)



            # 显示当前用户
            if user_manager.current_user:
                user_text = FONTS["small"].render(f"玩家: {user_manager.current_user['username']}", True, GREEN)
                screen.blit(user_text, (WIDTH - user_text.get_width() - 10, HEIGHT - 30))

            # 显示控制提示
            controls_text = FONTS["small"].render("ESC: 退出游戏  P: 个人统计", True, CYAN)
            screen.blit(controls_text, (WIDTH // 2 - controls_text.get_width() // 2, 10))

            # 显示难度提示
            if 2 <= difficulty_level <= 3:
                warning_text = FONTS["normal"].render("警告：高难度敌机出现！", True, ORANGE)
                screen.blit(warning_text, (WIDTH // 2 - warning_text.get_width() // 2, 50))

            if boss:
                warning_text = FONTS["normal"].render("警告：BOSS出现！", True, ORANGE)
                screen.blit(warning_text, (WIDTH // 2 - warning_text.get_width() // 2, 50))



        elif current_screen == "game_over":
            # 绘制游戏结束界面
            screen.fill(BLACK)

            # 绘制星星背景
            for i in range(100):
                x = random.randint(0, WIDTH)
                y = random.randint(0, HEIGHT)
                size = random.randint(1, 2)
                pygame.draw.circle(screen, WHITE, (x, y), size)

            # 绘制半透明覆盖层
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            # 绘制游戏结束文本
            game_over_text = FONTS["large"].render("游戏结束", True, RED)
            score_text = FONTS["medium"].render(f"最终得分：{final_score}", True, WHITE)
            time_text = FONTS["medium"].render(f"存活时间：{final_game_time}秒", True, WHITE)
            difficulty_text = FONTS["medium"].render(f"最终难度：{final_difficulty}", True, WHITE)
            damage_text = FONTS["medium"].render(f"子弹伤害：{final_bullet_damage}", True, YELLOW)
            enemies_text = FONTS["medium"].render(f"击败敌机：{final_enemies_killed}", True, GREEN)

            # 绘制保存状态
            save_status = ""
            if user_manager.current_user:
                save_status = "分数已保存到数据库"
                save_color = GREEN
            else:
                save_status = "游客模式，分数未保存"
                save_color = ORANGE

            save_text = FONTS["normal"].render(save_status, True, save_color)
            restart_text = FONTS["normal"].render("点击屏幕重新开始", True, GREEN)

            # 居中显示所有文本
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, 150))
            screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 220))
            screen.blit(time_text, (WIDTH // 2 - time_text.get_width() // 2, 270))
            screen.blit(difficulty_text, (WIDTH // 2 - difficulty_text.get_width() // 2, 320))
            screen.blit(damage_text, (WIDTH // 2 - damage_text.get_width() // 2, 370))
            screen.blit(enemies_text, (WIDTH // 2 - enemies_text.get_width() // 2, 420))
            screen.blit(save_text, (WIDTH // 2 - save_text.get_width() // 2, 480))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, 530))

            # 绘制返回登录按钮
            back_btn = pygame.Rect(WIDTH // 2 - 100, 600, 200, 40)
            pygame.draw.rect(screen, BLUE, back_btn)
            back_text = FONTS["normal"].render("返回登录界面", True, WHITE)
            screen.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, 610))

            # 检查返回登录按钮点击
            if pygame.mouse.get_pressed()[0] and back_btn.collidepoint(pygame.mouse.get_pos()):
                if current_time - last_click_time > click_cooldown:
                    game_resources.play_sound('click')
                    last_click_time = current_time
                current_screen = "login"

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()