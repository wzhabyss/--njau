import sqlite3 
 
conn = sqlite3.connect("plane_game.db") 
cursor = conn.cursor() 
 
cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)") 
 
cursor.execute("CREATE TABLE IF NOT EXISTS user_stats (user_id INTEGER PRIMARY KEY, total_games INTEGER DEFAULT 0, total_score INTEGER DEFAULT 0, highest_score INTEGER DEFAULT 0, last_played TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id))") 
 
cursor.execute("CREATE TABLE IF NOT EXISTS game_records (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, score INTEGER NOT NULL, game_duration INTEGER, enemies_defeated INTEGER, played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id))") 
 
cursor.execute("CREATE TABLE IF NOT EXISTS scores (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, score INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)") 
 
conn.commit() 
conn.close() 
print("✅ 本地数据库已创建：plane_game.db") 
print("🎮 可以运行游戏了！") 
