import numpy as np
import matplotlib.pyplot as plt

def process_and_plot(signal_ori, sample_rate, ax_waveform=None, ax_spectrum=None, show_plots=True, persistent_plot=False):
    """
    對原始信號進行傅立葉轉換並更新或生成圖表。
    參數：
    - signal_ori: 原始音訊信號
    - sample_rate: 採樣率
    - ax_waveform: 用於即時波形更新的 matplotlib 軸（可選）
    - ax_spectrum: 用於即時頻譜更新的 matplotlib 軸（可選）
    - show_plots: 是否顯示靜態圖表（預設為 True）
    - persistent_plot: 是否持續顯示圖表直到手動關閉（適用於即時模式）
    返回值：
    - frequencies: 頻率數據
    - magnitudes_db: 幅度譜數據（dB）
    """
    # 進行傅立葉轉換
    signal_fft = np.fft.fft(signal_ori)
    frequencies = np.fft.fftfreq(len(signal_ori), d=1/sample_rate)
    
    # 只取前半部分頻譜
    n = len(signal_ori)
    signal_fft = signal_fft[:n//2]
    frequencies = frequencies[:n//2]
    
    # 計算幅度和相位
    magnitudes = np.abs(signal_fft)
    magnitudes_db = 20 * np.log10(np.maximum(magnitudes, 1e-10))  # 防止 log(0)
    phases = np.unwrap(np.angle(signal_fft))  # 防止相位跳變
    
    if ax_waveform is not None and ax_spectrum is not None:
        # 更新即時波形圖
        ax_waveform.cla()
        time_axis = np.arange(len(signal_ori)) / sample_rate
        ax_waveform.plot(time_axis, signal_ori, color='blue')
        ax_waveform.set_title('Real-Time Waveform')
        ax_waveform.set_xlabel('Time (s)')
        ax_waveform.set_ylabel('Amplitude')
        
        # 更新即時頻譜圖
        ax_spectrum.cla()
        ax_spectrum.plot(frequencies, magnitudes_db, color='red')
        ax_spectrum.set_title('Real-Time Frequency Spectrum')
        ax_spectrum.set_xlabel('Frequency (Hz)')
        ax_spectrum.set_ylabel('Magnitude (dB)')
    
    elif show_plots:
        # 生成並顯示靜態圖表（僅用於除即時模式以外的情況）
        plt.figure()
        time_axis = np.arange(len(signal_ori)) / sample_rate
        plt.plot(time_axis, signal_ori)
        plt.title('Original Waveform')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude')
        plt.show()
        
        plt.figure()
        plt.plot(frequencies, magnitudes_db)
        plt.title('Magnitude Spectrum')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Magnitude (dB)')
        plt.show()
        
        plt.figure()
        plt.plot(frequencies, phases)
        plt.title('Phase Spectrum')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Phase (radians)')
        plt.show()
    
    return frequencies, magnitudes_db

def plot_spectrogram(signal_history, sample_rate, ax_spectrogram, draw_colorbar=False):
    """
    根據累積的音訊數據繪製频谱图（Spectrogram），並可選在旁邊加上 colorbar。
    
    參數：
    - signal_history: 包含歷史音訊數據的 1D numpy 陣列
    - sample_rate: 採樣率
    - ax_spectrogram: 用於顯示频谱图的 matplotlib 軸
    - draw_colorbar: 是否在圖表旁加入 colorbar（預設為 False）
    """
    ax_spectrogram.cla()
    NFFT = 256
    noverlap = 128

    spec, freqs, bins, im = ax_spectrogram.specgram(
        signal_history,
        NFFT=NFFT,
        Fs=sample_rate,
        noverlap=noverlap,
        cmap='jet'
    )
    # 設定圖像平滑效果
    im.set_interpolation('bilinear')

    # 當 draw_colorbar 為 True 時加入 colorbar
    if draw_colorbar:
        cbar = ax_spectrogram.figure.colorbar(im, ax=ax_spectrogram)
        cbar.set_label('Amplitude (dB)')

    ax_spectrogram.set_title('Spectrogram')
    ax_spectrogram.set_xlabel('Time (s)')
    ax_spectrogram.set_ylabel('Frequency (Hz)')

    
