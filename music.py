import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
from scipy import signal


def generate_clock_tick(duration=0.15, sample_rate=44100, frequency=3000):
    """生成单个钟表滴答声"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # 创建主要频率成分
    main_wave = np.sin(2 * np.pi * frequency * t)

    # 添加高频谐波
    harmonics = 0.3 * np.sin(2 * np.pi * frequency * 2 * t)

    # 添加轻微的金属共鸣
    metallic = 0.1 * np.sin(2 * np.pi * 80 * t) * np.exp(-10 * t)

    # 组合所有成分
    tick = main_wave + harmonics + metallic

    # 应用包络：快速起音，缓慢衰减
    envelope = np.exp(-15 * t) * (1 - np.exp(-200 * t))

    # 应用指数衰减包络
    tick = tick * envelope

    # 归一化
    tick = tick / np.max(np.abs(tick)) * 0.7

    return tick


def generate_pendulum_swing(duration=2.0, sample_rate=44100):
    """生成钟摆摆动声"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # 低频摆动基础音
    base_freq = 0.5  # 0.5Hz，2秒一个周期
    swing = 0.3 * np.sin(2 * np.pi * base_freq * t)

    # 添加机械摩擦声
    friction = 0.05 * np.random.normal(0, 1, len(t)) * np.exp(-0.5 * t)

    # 组合
    pendulum = swing + friction

    # 应用包络
    envelope = np.exp(-0.5 * t)
    pendulum = pendulum * envelope

    return pendulum


def generate_background_ambience(duration, sample_rate=44100):
    """生成背景环境音"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # 非常低频的嗡鸣声（类似机械运转）
    hum = 0.02 * np.sin(2 * np.pi * 30 * t)

    # 轻微的白噪声（类似空气流动）
    noise = 0.01 * np.random.normal(0, 1, len(t))

    # 偶尔的机械脉冲
    pulses = np.zeros(len(t))
    pulse_times = np.arange(1.0, duration, 3.0)  # 每3秒一个脉冲
    for pt in pulse_times:
        idx = int(pt * sample_rate)
        if idx < len(pulses):
            pulse_len = int(0.1 * sample_rate)
            pulse = 0.05 * np.exp(-50 * np.linspace(0, 0.1, pulse_len))
            end_idx = min(idx + pulse_len, len(pulses))
            pulses[idx:end_idx] += pulse[:end_idx - idx]

    ambience = hum + noise + pulses

    return ambience


def generate_zawaludo_clock_sound(duration=9.0, sample_rate=44100):
    """生成完整的砸瓦鲁多钟表音效"""
    # 创建时间轴
    total_samples = int(duration * sample_rate)
    audio = np.zeros(total_samples)

    # 添加背景环境音
    print("生成背景环境音...")
    ambience = generate_background_ambience(duration, sample_rate)
    audio += ambience

    # 生成钟表滴答声序列
    print("生成钟表滴答声...")
    tick_interval = 1.0  # 每秒一个滴答
    num_ticks = int(duration / tick_interval)

    for i in range(num_ticks):
        # 交替的滴答声（模仿钟表左右摆动）
        if i % 2 == 0:
            tick = generate_clock_tick(frequency=2800)  # 较高音
        else:
            tick = generate_clock_tick(frequency=2500)  # 较低音

        # 计算滴答声的位置
        start_sample = int(i * tick_interval * sample_rate)
        end_sample = start_sample + len(tick)

        # 确保不超出音频长度
        if end_sample < len(audio):
            audio[start_sample:end_sample] += tick * 0.8

    # 添加钟摆摆动声（逐渐出现）
    print("生成钟摆摆动声...")
    pendulum_start = 1.0  # 第1秒开始
    pendulum_duration = duration - pendulum_start
    pendulum = generate_pendulum_swing(pendulum_duration, sample_rate)

    start_idx = int(pendulum_start * sample_rate)
    end_idx = start_idx + len(pendulum)

    if end_idx <= len(audio):
        audio[start_idx:end_idx] += pendulum

    # 添加时间停止的"嗡"声效果（在第6秒开始）
    print("添加时间停止效果...")
    stop_time = 6.0
    stop_duration = 1.0
    stop_samples = int(stop_duration * sample_rate)
    stop_start = int(stop_time * sample_rate)

    # 创建时间停止的低频嗡鸣
    t_stop = np.linspace(0, stop_duration, stop_samples, False)
    stop_hum = 0.15 * np.sin(2 * np.pi * 120 * t_stop) * np.exp(-1 * t_stop)

    # 添加高频衰减
    stop_high = 0.1 * np.sin(2 * np.pi * 4000 * t_stop) * np.exp(-10 * t_stop)

    stop_effect = stop_hum + stop_high

    # 叠加到主音频
    end_stop = min(stop_start + len(stop_effect), len(audio))
    audio[stop_start:end_stop] += stop_effect[:end_stop - stop_start]

    # 最后添加强烈的结束滴答声
    print("添加结束音...")
    final_tick = generate_clock_tick(duration=0.3, frequency=3200)
    final_tick = final_tick * np.exp(-5 * np.linspace(0, 0.3, len(final_tick)))

    final_start = int((duration - 0.5) * sample_rate)  # 结束前0.5秒
    final_end = min(final_start + len(final_tick), len(audio))
    audio[final_start:final_end] += final_tick[:final_end - final_start] * 0.9

    # 归一化
    print("处理音频...")
    audio = audio / np.max(np.abs(audio)) * 0.95

    # 添加淡入淡出
    fade_samples = int(0.1 * sample_rate)  # 100ms淡入淡出
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)

    audio[:fade_samples] *= fade_in
    audio[-fade_samples:] *= fade_out

    return audio


def save_and_visualize(audio, filename, sample_rate=44100):
    """保存音频文件并生成可视化"""
    # 保存为WAV文件
    print(f"保存音频文件: {filename}")
    sf.write(filename, audio, sample_rate)

    # 生成波形图
    plt.figure(figsize=(12, 8))

    # 波形图
    plt.subplot(3, 1, 1)
    time = np.linspace(0, len(audio) / sample_rate, len(audio))
    plt.plot(time, audio, 'b', alpha=0.7, linewidth=0.5)
    plt.title('ZAWARUDO 钟表音效 - 波形图', fontsize=14, fontweight='bold')
    plt.xlabel('时间 (秒)')
    plt.ylabel('振幅')
    plt.grid(True, alpha=0.3)

    # 频谱图
    plt.subplot(3, 1, 2)
    frequencies, times, spectrogram = signal.spectrogram(
        audio,
        sample_rate,
        nperseg=1024,
        noverlap=512
    )
    plt.pcolormesh(times, frequencies, 10 * np.log10(spectrogram),
                   shading='gouraud', cmap='viridis')
    plt.title('频谱图', fontsize=14)
    plt.ylabel('频率 (Hz)')
    plt.xlabel('时间 (秒)')
    plt.ylim(0, 5000)
    plt.colorbar(label='强度 (dB)')

    # 包络图
    plt.subplot(3, 1, 3)
    envelope = np.abs(signal.hilbert(audio))
    smoothed_envelope = np.convolve(envelope, np.ones(1000) / 1000, mode='same')
    plt.plot(time, smoothed_envelope, 'r', linewidth=2)
    plt.title('音频包络', fontsize=14)
    plt.xlabel('时间 (秒)')
    plt.ylabel('振幅')
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('zawarudo_audio_analysis.png', dpi=150, bbox_inches='tight')
    plt.show()


def main():
    """主函数"""
    print("开始生成 ZAWARUDO 钟表音效...")
    print("=" * 50)

    # 参数设置
    duration = 9.0  # 音频时长（秒）
    sample_rate = 44100  # 采样率
    filename = "zawarudo_clock_sound.wav"

    # 生成音频
    audio = generate_zawaludo_clock_sound(duration, sample_rate)

    # 保存并可视化
    save_and_visualize(audio, filename, sample_rate)

    print("\n" + "=" * 50)
    print("音效生成完成！")
    print(f"音频文件已保存为: {filename}")
    print(f"频谱图已保存为: zawarudo_audio_analysis.png")
    print(f"时长: {duration}秒")
    print(f"采样率: {sample_rate}Hz")


if __name__ == "__main__":
    main()