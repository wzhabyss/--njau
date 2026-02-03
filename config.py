# config.py
# MySQL数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',      # 改为你的MySQL用户名
    'password': '',      # 改为你的MySQL密码
    'database': 'plane_game_db'
}

# 游戏配置
GAME_CONFIG = {
    'window_width': 800,
    'window_height': 600,
    'fps': 60
}

# 在config.py末尾添加：
BOSS_CONFIG = {
    'width': 80,
    'height': 80,
    'initial_hp': 50,
    'hp_increment': 30,
    'initial_damage': 2,
    'damage_increment': 1,
    'initial_speed': 3,
    'speed_increment': 0.5,
    'spawn_minute': 5,  # 每5分钟生成
    'color': (255, 0, 0)  # 红色Boss
}