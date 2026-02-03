@echo off
chcp 65001 >nul
cls
echo ╔═══════════════════════════════════════╗
echo ║      最简单打包方法（跳过依赖）       ║
echo ╚═══════════════════════════════════════╝
echo.

echo [1/4] 清理旧文件...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec" del *.spec
echo ✅ 清理完成

echo.
echo [2/4] 直接打包（不安装依赖）...
echo 注意：如果打包后运行缺少模块，游戏会提示
echo.

pyinstaller --onefile --name "planegame" --windowed ^
  --add-data "config.py;." ^
  --add-data "user.py;." ^
  --add-data "utils.py;." ^
  --add-data "resource.py;." ^
  --add-data "game_resources.py;." ^
  --add-data "fonts;fonts" ^
  --add-data "images;images" ^
  --add-data "sounds;sounds" ^
  --add-data "data;data" ^
  main.py

echo.
echo [3/4] 创建数据库替代方案...
REM 创建本地数据库文件
echo import sqlite3 > create_local_db.py
echo. >> create_local_db.py
echo conn = sqlite3.connect("plane_game.db") >> create_local_db.py
echo cursor = conn.cursor() >> create_local_db.py
echo. >> create_local_db.py
echo cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)") >> create_local_db.py
echo. >> create_local_db.py
echo cursor.execute("CREATE TABLE IF NOT EXISTS user_stats (user_id INTEGER PRIMARY KEY, total_games INTEGER DEFAULT 0, total_score INTEGER DEFAULT 0, highest_score INTEGER DEFAULT 0, last_played TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id))") >> create_local_db.py
echo. >> create_local_db.py
echo cursor.execute("CREATE TABLE IF NOT EXISTS game_records (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, score INTEGER NOT NULL, game_duration INTEGER, enemies_defeated INTEGER, played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id))") >> create_local_db.py
echo. >> create_local_db.py
echo cursor.execute("CREATE TABLE IF NOT EXISTS scores (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, score INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)") >> create_local_db.py
echo. >> create_local_db.py
echo conn.commit() >> create_local_db.py
echo conn.close() >> create_local_db.py
echo print("✅ 本地数据库已创建：plane_game.db") >> create_local_db.py
echo print("🎮 可以运行游戏了！") >> create_local_db.py
echo ✅ 数据库脚本创建完成

echo.
echo [4/4] 创建便捷启动包...
if exist "dist\planegame.exe" (
    echo 正在创建启动文件...

    REM 先复制数据库脚本
    copy "create_local_db.py" "dist\" >nul

    REM 创建启动脚本 - 使用更简单的方法
    echo @echo off > "dist\启动游戏.bat"
    echo chcp 65001 ^>nul >> "dist\启动游戏.bat"
    echo cls >> "dist\启动游戏.bat"
    echo echo. >> "dist\启动游戏.bat"
    echo echo ======================================== >> "dist\启动游戏.bat"
    echo echo     飞机大战游戏启动器 >> "dist\启动游戏.bat"
    echo echo ======================================== >> "dist\启动游戏.bat"
    echo echo. >> "dist\启动游戏.bat"
    echo echo 请选择操作： >> "dist\启动游戏.bat"
    echo echo. >> "dist\启动游戏.bat"
    echo echo [1] 启动游戏（推荐） >> "dist\启动游戏.bat"
    echo echo [2] 创建/重置数据库 >> "dist\启动游戏.bat"
    echo echo [3] 退出 >> "dist\启动游戏.bat"
    echo echo. >> "dist\启动游戏.bat"
    echo set /p choice=请输入选择（1-3）: >> "dist\启动游戏.bat"
    echo. >> "dist\启动游戏.bat"
    echo if "%%choice%%"=="1" goto start_game >> "dist\启动游戏.bat"
    echo if "%%choice%%"=="2" goto create_db >> "dist\启动游戏.bat"
    echo if "%%choice%%"=="3" exit >> "dist\启动游戏.bat"
    echo echo 无效选择 >> "dist\启动游戏.bat"
    echo pause >> "dist\启动游戏.bat"
    echo exit >> "dist\启动游戏.bat"
    echo. >> "dist\启动游戏.bat"
    echo :start_game >> "dist\启动游戏.bat"
    echo echo 正在启动游戏... >> "dist\启动游戏.bat"
    echo timeout /t 1 /nobreak ^>nul >> "dist\启动游戏.bat"
    echo start "" "planegame.exe" >> "dist\启动游戏.bat"
    echo exit >> "dist\启动游戏.bat"
    echo. >> "dist\启动游戏.bat"
    echo :create_db >> "dist\启动游戏.bat"
    echo echo 正在创建数据库... >> "dist\启动游戏.bat"
    echo python create_local_db.py >> "dist\启动游戏.bat"
    echo echo. >> "dist\启动游戏.bat"
    echo echo 按任意键返回... >> "dist\启动游戏.bat"
    echo pause ^>nul >> "dist\启动游戏.bat"
    echo goto :menu >> "dist\启动游戏.bat"
    echo :menu >> "dist\启动游戏.bat"

    REM 创建说明文件
    echo 飞机大战游戏 - 使用说明 > "dist\使用说明.txt"
    echo ======================== >> "dist\使用说明.txt"
    echo. >> "dist\使用说明.txt"
    echo 1. 首次运行： >> "dist\使用说明.txt"
    echo    - 双击"启动游戏.bat" >> "dist\使用说明.txt"
    echo    - 选择 [1] 启动游戏 >> "dist\使用说明.txt"
    echo    - 游戏会自动创建数据库 >> "dist\使用说明.txt"
    echo. >> "dist\使用说明.txt"
    echo 2. 如果游戏提示缺少数据库： >> "dist\使用说明.txt"
    echo    - 选择 [2] 创建/重置数据库 >> "dist\使用说明.txt"
    echo    - 然后再次启动游戏 >> "dist\使用说明.txt"
    echo. >> "dist\使用说明.txt"
    echo 3. 如果提示缺少模块： >> "dist\使用说明.txt"
    echo    - 记录下缺少的模块名称 >> "dist\使用说明.txt"
    echo    - 运行：pip install 模块名 >> "dist\使用说明.txt"
    echo    - 重新打包游戏 >> "dist\使用说明.txt"
    echo. >> "dist\使用说明.txt"
    echo 4. 直接运行： >> "dist\使用说明.txt"
    echo    - 也可以直接双击"planegame.exe" >> "dist\使用说明.txt"
    echo    - 但建议使用"启动游戏.bat" >> "dist\使用说明.txt"
    echo. >> "dist\使用说明.txt"
    echo 提示：确保游戏文件夹中有以下子文件夹： >> "dist\使用说明.txt"
    echo     - fonts/   字体文件 >> "dist\使用说明.txt"
    echo     - images/  游戏图片 >> "dist\使用说明.txt"
    echo     - sounds/  游戏音效 >> "dist\使用说明.txt"
    echo     - data/    游戏数据 >> "dist\使用说明.txt"
    echo. >> "dist\使用说明.txt"
    echo 游戏愉快！ >> "dist\使用说明.txt"

    echo ✅ 打包完成！
    echo.
    echo 📂 游戏文件位于：dist 文件夹
    echo.
    echo 📄 包含文件：
    echo    - planegame.exe     （主程序）
    echo    - 启动游戏.bat      （启动器）
    echo    - 使用说明.txt      （说明文档）
    echo    - create_local_db.py（数据库工具）
    echo.
    echo 🎮 运行方法：
    echo 1. 进入 dist 文件夹
    echo 2. 双击 "启动游戏.bat"
    echo 3. 选择 [1] 启动游戏
    echo.
    echo 💡 可能的解决方案：
    echo - 如果缺少mysql.connector：游戏会自动使用本地模式
    echo - 如果缺少其他模块：请记录模块名并告诉我
    echo - 如果游戏闪退：先运行数据库创建工具（选项2）
    echo.
    echo 🔧 故障排除：
    echo 1. 确保所有资源文件夹存在（fonts, images, sounds, data）
    echo 2. 如果提示权限问题，以管理员身份运行
    echo 3. 确保杀毒软件没有阻止游戏运行
) else (
    echo ❌ 打包失败，请检查错误信息
)

echo.
pause