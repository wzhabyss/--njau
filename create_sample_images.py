# create_sample_images.py
import pygame
import os

# 初始化Pygame
pygame.init()

# 创建images目录
os.makedirs('images', exist_ok=True)

# 1. 玩家飞机图像
player_surf = pygame.Surface((50, 40), pygame.SRCALPHA)
# 飞机主体（三角形）
points = [(25, 0), (0, 40), (50, 40)]
pygame.draw.polygon(player_surf, (0, 120, 255), points)
# 机翼
pygame.draw.rect(player_surf, (0, 120, 255), (15, 20, 20, 10))
pygame.image.save(player_surf, 'images/player.png')

# 2. 敌机图像
enemy_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
points = [(20, 40), (0, 0), (40, 0)]
pygame.draw.polygon(enemy_surf, (255, 50, 50), points)
pygame.draw.rect(enemy_surf, (255, 50, 50), (10, 15, 20, 8))
pygame.image.save(enemy_surf, 'images/enemy.png')

# 3. 子弹图像
bullet_surf = pygame.Surface((5, 15), pygame.SRCALPHA)
pygame.draw.rect(bullet_surf, (255, 255, 0), (0, 0, 5, 15))
pygame.draw.rect(bullet_surf, (255, 200, 0), (1, 1, 3, 13))
pygame.image.save(bullet_surf, 'images/bullet.png')

# 4. 血包图像
health_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
# 红色十字
pygame.draw.rect(health_surf, (0, 255, 0), (10, 0, 10, 30))
pygame.draw.rect(health_surf, (0, 255, 0), (0, 10, 30, 10))
# 白色边框
pygame.draw.rect(health_surf, (255, 255, 255), (0, 0, 30, 30), 2)
pygame.image.save(health_surf, 'images/health_pack.png')

# 5. 子弹包图像
bullet_pack_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
# 粉色三角形
points = [(15, 5), (5, 25), (25, 25)]
pygame.draw.polygon(bullet_pack_surf, (255, 105, 180), points)
# 加号
pygame.draw.rect(bullet_pack_surf, (255, 255, 255), (10, 13, 10, 4))
pygame.draw.rect(bullet_pack_surf, (255, 255, 255), (13, 10, 4, 10))
pygame.draw.rect(bullet_pack_surf, (255, 255, 255), (0, 0, 30, 30), 2)
pygame.image.save(bullet_pack_surf, 'images/bullet_pack.png')

# 6. 背景图像
bg_surf = pygame.Surface((100, 100))
# 星星背景
for i in range(50):
    x = pygame.time.get_ticks() % 100  # 随机位置
    y = (i * 7) % 100
    size = 1 if i % 3 == 0 else 2
    pygame.draw.circle(bg_surf, (255, 255, 255), (x, y), size)
pygame.image.save(bg_surf, 'images/background.png')

# 7. 按钮图像
button_surf = pygame.Surface((200, 50), pygame.SRCALPHA)
# 渐变按钮
for i in range(50):
    color = (0, 150 + i, 255 - i*2)
    pygame.draw.rect(button_surf, color, (0, i, 200, 1))
# 边框
pygame.draw.rect(button_surf, (255, 255, 255), (0, 0, 200, 50), 2)
pygame.image.save(button_surf, 'images/button.png')

# 8. 爆炸效果图像（序列帧）
for i in range(5):
    explosion_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
    radius = i * 5 + 10
    color = (255, 100 + i*30, 0)
    pygame.draw.circle(explosion_surf, color, (25, 25), radius)
    pygame.draw.circle(explosion_surf, (255, 255, 100), (25, 25), radius-3)
    pygame.image.save(explosion_surf, f'images/explosion_{i}.png')

print("✅ 示例图像已创建在 images/ 目录")