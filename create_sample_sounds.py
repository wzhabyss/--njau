# create_sample_sounds.py
import pygame
import numpy as np
import os

pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# 创建sounds目录
os.makedirs('sounds', exist_ok=True)


def generate_sound(frequency, duration, volume=0.5, sound_type='sine'):
    """生成简单音效"""
    sample_rate = 22050
    n_samples = int(round(duration * sample_rate))

    # 生成时间序列
    buf = np.zeros((n_samples, 2), dtype=np.int16)
    max_sample = 2 ** (16 - 1) - 1

    for s in range(n_samples):
        t = float(s) / sample_rate

        if sound_type == 'sine':
            sample = volume * max_sample * np.sin(2 * np.pi * frequency * t)
        elif sound_type == 'square':
            sample = volume * max_sample * np.sign(np.sin(2 * np.pi * frequency * t))
        elif sound_type == 'sawtooth':
            sample = volume * max_sample * (2 * (t * frequency - np.floor(0.5 + t * frequency)))
        else:  # triangle
            sample = volume * max_sample * 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1

        # 添加衰减
        if s > n_samples * 0.9:
            sample *= (1.0 - (s - n_samples * 0.9) / (n_samples * 0.1))

        buf[s][0] = int(sample)
        buf[s][1] = int(sample)

    return pygame.sndarray.make_sound(buf)


# 1. 射击音效
shoot_sound = generate_sound(880, 0.1, 0.3, 'sine')
pygame.mixer.Sound.save(shoot_sound, 'sounds/shoot.wav')

# 2. 爆炸音效
explosion_sound = generate_sound(110, 0.3, 0.5, 'sawtooth')
pygame.mixer.Sound.save(explosion_sound, 'sounds/explosion.wav')

# 3. 击中音效
hit_sound = generate_sound(440, 0.05, 0.4, 'square')
pygame.mixer.Sound.save(hit_sound, 'sounds/hit.wav')

# 4. 获得道具音效
powerup_sound = generate_sound(660, 0.15, 0.3, 'triangle')
pygame.mixer.Sound.save(powerup_sound, 'sounds/powerup.wav')

# 5. 按钮点击音效
click_sound = generate_sound(220, 0.08, 0.2, 'sine')
pygame.mixer.Sound.save(click_sound, 'sounds/click.wav')

# 6. 游戏结束音效
gameover_sound = generate_sound(165, 0.5, 0.4, 'sawtooth')
pygame.mixer.Sound.save(gameover_sound, 'sounds/gameover.wav')

print("✅ 示例音效已创建在 sounds/ 目录")

# 注意：实际游戏建议使用真实音效文件，这些只是示例