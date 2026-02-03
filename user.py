# user.py
import mysql.connector
from mysql.connector import Error
import hashlib
import datetime
from typing import Optional, Tuple, List, Dict


class UserManager:
    def __init__(self, host: str = "localhost", user: str = "root",
                 password: str = "", database: str = "plane_game_db"):
        """
        初始化用户管理器

        Args:
            host: MySQL主机地址
            user: MySQL用户名
            password: MySQL密码
            database: 数据库名称
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.current_user = None  # 当前登录用户
        self.connect()
        self.create_tables()

    def connect(self) -> bool:
        """连接到MySQL数据库"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                print("成功连接到MySQL数据库")
                self.cursor = self.connection.cursor()
                return True
        except Error as e:
            print(f"连接数据库失败: {e}")
            # 如果数据库不存在，尝试创建它
            try:
                conn = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password
                )
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
                conn.close()

                # 重新连接
                self.connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
                )
                self.cursor = self.connection.cursor()
                print("成功创建并连接到数据库")
                return True
            except Error as e2:
                print(f"创建数据库失败: {e2}")
                return False
        return False

    def create_tables(self):
        """创建必要的数据库表"""
        try:
            # 创建用户表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL
                )
            """)

            # 创建游戏记录表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    score INT NOT NULL,
                    difficulty_level INT NOT NULL,
                    game_time INT NOT NULL,  # 游戏时间（秒）
                    bullet_damage INT NOT NULL DEFAULT 1,
                    enemies_killed INT DEFAULT 0,
                    date_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # 创建用户统计表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INT PRIMARY KEY,
                    total_games INT DEFAULT 0,
                    total_score BIGINT DEFAULT 0,
                    highest_score INT DEFAULT 0,
                    total_game_time INT DEFAULT 0,
                    highest_difficulty INT DEFAULT 0,
                    last_played TIMESTAMP NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            self.connection.commit()
            print("数据库表创建成功")

        except Error as e:
            print(f"创建表失败: {e}")

    def hash_password(self, password: str) -> str:
        """对密码进行哈希处理"""
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username: str, password: str, email: str = "") -> Tuple[bool, str]:
        """
        注册新用户

        Args:
            username: 用户名
            password: 密码
            email: 邮箱（可选）

        Returns:
            (成功状态, 消息)
        """
        try:
            # 检查用户名是否已存在
            self.cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if self.cursor.fetchone():
                return False, "用户名已存在"

            # 哈希密码
            password_hash = self.hash_password(password)

            # 插入新用户
            self.cursor.execute("""
                INSERT INTO users (username, password_hash, email)
                VALUES (%s, %s, %s)
            """, (username, password_hash, email))

            user_id = self.cursor.lastrowid

            # 初始化用户统计
            self.cursor.execute("""
                INSERT INTO user_stats (user_id)
                VALUES (%s)
            """, (user_id,))

            self.connection.commit()
            return True, "注册成功"

        except Error as e:
            print(f"注册失败: {e}")
            return False, f"注册失败: {str(e)}"

    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        用户登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            (成功状态, 消息)
        """
        try:
            password_hash = self.hash_password(password)

            self.cursor.execute("""
                SELECT id, username FROM users 
                WHERE username = %s AND password_hash = %s
            """, (username, password_hash))

            user = self.cursor.fetchone()
            if user:
                self.current_user = {
                    'id': user[0],
                    'username': user[1]
                }

                # 更新最后登录时间
                self.cursor.execute("""
                    UPDATE users SET last_login = NOW() 
                    WHERE id = %s
                """, (user[0],))
                self.connection.commit()

                return True, "登录成功"
            else:
                return False, "用户名或密码错误"

        except Error as e:
            print(f"登录失败: {e}")
            return False, f"登录失败: {str(e)}"

    def logout(self):
        """用户登出"""
        self.current_user = None

    def save_game_record(self, score: int, difficulty_level: int,
                         game_time: int, bullet_damage: int, enemies_killed: int = 0) -> bool:
        """
        保存游戏记录

        Args:
            score: 游戏得分
            difficulty_level: 难度等级
            game_time: 游戏时间（秒）
            bullet_damage: 最终子弹伤害
            enemies_killed: 击败敌人数（可选）

        Returns:
            保存是否成功
        """
        if not self.current_user:
            return False

        try:
            user_id = self.current_user['id']

            # 插入游戏记录
            self.cursor.execute("""
                INSERT INTO game_records 
                (user_id, score, difficulty_level, game_time, bullet_damage, enemies_killed)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, score, difficulty_level, game_time, bullet_damage, enemies_killed))

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
            """, (difficulty_level, user_id))

            self.connection.commit()
            return True

        except Error as e:
            print(f"保存游戏记录失败: {e}")
            return False

    def get_user_stats(self) -> Optional[Dict]:
        """
        获取当前用户的统计数据

        Returns:
            用户统计字典，如果用户未登录则返回None
        """
        if not self.current_user:
            return None

        try:
            user_id = self.current_user['id']

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

        except Error as e:
            print(f"获取用户统计失败: {e}")
            return None

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """
        获取排行榜

        Args:
            limit: 返回的记录数量

        Returns:
            排行榜列表
        """
        try:
            self.cursor.execute("""
                SELECT u.username, g.score, g.difficulty_level, 
                       g.game_time, g.date_played
                FROM game_records g
                JOIN users u ON g.user_id = u.id
                ORDER BY g.score DESC
                LIMIT %s
            """, (limit,))

            records = self.cursor.fetchall()
            leaderboard = []

            for i, record in enumerate(records):
                leaderboard.append({
                    'rank': i + 1,
                    'username': record[0],
                    'score': record[1],
                    'difficulty_level': record[2],
                    'game_time': record[3],
                    'date_played': record[4]
                })

            return leaderboard

        except Error as e:
            print(f"获取排行榜失败: {e}")
            return []

    def get_user_game_history(self, limit: int = 10) -> List[Dict]:
        """
        获取当前用户的游戏历史

        Args:
            limit: 返回的记录数量

        Returns:
            游戏历史列表
        """
        if not self.current_user:
            return []

        try:
            user_id = self.current_user['id']

            self.cursor.execute("""
                SELECT score, difficulty_level, game_time, 
                       bullet_damage, enemies_killed, date_played
                FROM game_records
                WHERE user_id = %s
                ORDER BY date_played DESC
                LIMIT %s
            """, (user_id, limit))

            records = self.cursor.fetchall()
            history = []

            for record in records:
                history.append({
                    'score': record[0],
                    'difficulty_level': record[1],
                    'game_time': record[2],
                    'bullet_damage': record[3],
                    'enemies_killed': record[4],
                    'date_played': record[5]
                })

            return history

        except Error as e:
            print(f"获取游戏历史失败: {e}")
            return []

    def close(self):
        """关闭数据库连接"""
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("数据库连接已关闭")

    def __del__(self):
        """析构函数，确保连接被关闭"""
        self.close()