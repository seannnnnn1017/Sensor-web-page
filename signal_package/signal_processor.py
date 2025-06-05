import numpy as np
import matplotlib.pyplot as plt

def process_and_plot(signal_ori, sample_rate, ax_waveform=None, ax_spectrum=None, show_plots=True, persistent_plot=False):
    """
    對原始信號進行傅立葉轉換並更新或生成圖表。
    """
    try:
        # 進行傅立葉轉換
        signal_fft = np.fft.fft(signal_ori)
        frequencies = np.fft.fftfreq(len(signal_ori), d=1/sample_rate)

        # 只取前半部分頻譜
        n = len(signal_ori)
        signal_fft = signal_fft[:n//2]
        frequencies = frequencies[:n//2]

        # 計算幅度
        magnitudes = np.abs(signal_fft)
        magnitudes_db = 20 * np.log10(np.maximum(magnitudes, 1e-10))

        if ax_waveform is not None and ax_spectrum is not None:
            # 更新即時波形圖
            ax_waveform.clear()
            time_axis = np.arange(len(signal_ori)) / sample_rate
            ax_waveform.plot(time_axis, signal_ori, color='blue')
            ax_waveform.set_title('Real-Time Waveform')
            ax_waveform.set_xlabel('Time (s)')
            ax_waveform.set_ylabel('Amplitude')

            # 更新即時頻譜圖
            ax_spectrum.clear()
            ax_spectrum.plot(frequencies, magnitudes_db, color='red')
            ax_spectrum.set_title('Real-Time Frequency Spectrum')
            ax_spectrum.set_xlabel('Frequency (Hz)')
            ax_spectrum.set_ylabel('Magnitude (dB)')

        return frequencies, magnitudes_db

    except Exception as e:
        print(f"信號處理時發生錯誤: {e}")
        return np.array([]), np.array([])

def plot_spectrogram(signal_history, sample_rate, ax_spectrogram, draw_colorbar=False):
    """
    根據累積的音訊數據繪製频谱图
    """
    try:
        ax_spectrogram.clear()
        NFFT = 256
        noverlap = 128

        # 使用 matplotlib 的 specgram 函數生成頻譜圖
        spec, freqs, bins, im = ax_spectrogram.specgram(
            signal_history,
            NFFT=NFFT,
            Fs=sample_rate,
            noverlap=noverlap,
            cmap='jet'
        )

        # 確保 spec 是實數數據
        if np.iscomplexobj(spec):
            spec = np.abs(spec)

        # 確保數據類型是 float64
        spec = spec.astype(np.float64)
        freqs = freqs.astype(np.float64)
        bins = bins.astype(np.float64)

        # 設定圖像平滑效果
        im.set_interpolation('bilinear')

        # 當 draw_colorbar 為 True 時加入 colorbar
        if draw_colorbar:
            try:
                cbar = ax_spectrogram.figure.colorbar(im, ax=ax_spectrogram)
                cbar.set_label('Amplitude (dB)')
            except Exception as e:
                print(f"添加 colorbar 時出錯: {e}")

        ax_spectrogram.set_title('Spectrogram')
        ax_spectrogram.set_xlabel('Time (s)')
        ax_spectrogram.set_ylabel('Frequency (Hz)')

        return spec, freqs, bins

    except Exception as e:
        print(f"生成頻譜圖時發生錯誤: {e}")
        # 返回空數據以避免程序崩潰
        return np.array([[]]), np.array([]), np.array([])
