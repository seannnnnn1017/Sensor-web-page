import numpy as np
import matplotlib.pyplot as plt
from audio_recorder import AudioRecorder
from signal_processor import process_and_plot, plot_spectrogram
from audio_save import save_spectrogram_to_tdms
import datetime


def main():
    sample_rate = 22050
    duration = 10
    update_interval = 0.1
    history_duration = 100

    plt.ion()
    fig, ax = plt.subplots(3, 1, figsize=(10, 10))
    ax_waveform = ax[0]
    ax_spectrum = ax[1]
    ax_spectrogram = ax[2]

    audio_history = np.array([], dtype=np.int16)
    max_history_samples = int(history_duration * sample_rate)

    # 初始化錄音器
    recorder = AudioRecorder(sample_rate=sample_rate, channels=None, chunk=1024, verbose=True)

    num_iterations = int(duration / update_interval)
    for i in range(num_iterations):
        singel_ori = recorder.record_audio(update_interval)
        audio_history = np.concatenate((audio_history, singel_ori))
        if len(audio_history) > max_history_samples:
            audio_history = audio_history[-max_history_samples:]
        
        # 更新波形與頻譜圖 (不影響 colorbar)
        process_and_plot(
            singel_ori, sample_rate,
            ax_waveform=ax_waveform,
            ax_spectrum=ax_spectrum,
            show_plots=False
        )

        # 即時更新頻譜圖，但不加 colorbar
        plot_spectrogram(audio_history, sample_rate, ax_spectrogram, draw_colorbar=False)
        
        plt.pause(update_interval)

    # 錄音結束，關閉音訊串流
    recorder.close()

    # 生成最終頻譜圖並儲存數據
    spec, freqs, bins = plot_spectrogram(audio_history, sample_rate, ax_spectrogram, draw_colorbar=True)
    save_spectrogram_to_tdms(spec, freqs, bins, sample_rate, NFFT=256, noverlap=128, 
                         experiment_id="EXP_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                         filename='spectrogram.tdms')


    plt.ioff()
    plt.show()

if __name__ == '__main__':
    main()