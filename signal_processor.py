import numpy as np
import matplotlib.pyplot as plt

def process_and_plot(singel_ori, sample_rate):
    """
    對原始信號進行傅立葉轉換並生成圖表。
    參數：
    - singel_ori: 原始音訊信號
    - sample_rate: 採樣率
    """
    # 進行傅立葉轉換
    singel_fft = np.fft.fft(singel_ori)
    frequencies = np.fft.fftfreq(len(singel_ori), d=1/sample_rate)
    
    # 只取前半部分頻譜
    n = len(singel_ori)
    singel_fft = singel_fft[:n//2]
    frequencies = frequencies[:n//2]
    
    # 計算幅度和相位
    magnitudes = np.abs(singel_fft)
    phases = np.angle(singel_fft)
    magnitudes_db = 20 * np.log10(magnitudes + 1e-10)

    # 生成並顯示原始波形圖
    plt.figure()
    time = np.arange(len(singel_ori)) / sample_rate
    plt.plot(time, singel_ori)
    plt.title('Original Waveform')
    plt.xlabel('時間 (秒)')
    plt.ylabel('振幅')
    plt.show()

    # 生成並顯示幅度譜
    plt.figure()
    plt.plot(frequencies, magnitudes_db)
    plt.title('Magnitude Spectrum')
    plt.xlabel('頻率 (Hz)')
    plt.ylabel('幅度 (dB)')
    plt.show()

    # 生成並顯示相位譜
    plt.figure()
    plt.plot(frequencies, phases)
    plt.title('Phase Spectrum')
    plt.xlabel('頻率 (Hz)')
    plt.ylabel('相位 (弧度)')
    plt.show()