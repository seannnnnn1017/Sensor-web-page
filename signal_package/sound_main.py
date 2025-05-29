# sound_main.py

import numpy as np
import matplotlib.pyplot as plt
from audio_recorder import AudioRecorder # [1]
from signal_processor import process_and_plot, plot_spectrogram # [3]
# 修改: 從 audio_save 匯入 save_spectrogram_to_csv，如果仍需TDMS則保留 save_spectrogram_to_tdms
from audio_save import save_spectrogram_to_csv, save_spectrogram_to_tdms # [2]
import datetime
import time # 雖然原始碼沒有直接用 time，但 recorder.record_audio 內部可能用

def main():
    sample_rate = 22050
    duration = 10  # 總錄製時長（秒）
    update_interval = 0.1  # 每次錄製和更新圖表的間隔（秒）
    history_duration = 100  # 頻譜圖顯示的歷史數據時長（秒）

    plt.ion()  # 開啟互動模式

    # 創建三個子圖：波形、頻譜、頻譜圖
    fig, ax = plt.subplots(3, 1, figsize=(10, 12)) # 稍微調整 figsize 以容納標題和標籤
    ax_waveform = ax[0]
    ax_spectrum = ax[1]
    ax_spectrogram = ax[2]

    # 初始化音訊歷史數據陣列
    audio_history = np.array([], dtype=np.int16)
    max_history_samples = int(history_duration * sample_rate)

    # 初始化錄音器
    # AudioRecorder 會自動檢測可用的輸入設備和通道數
    recorder = AudioRecorder(sample_rate=sample_rate, channels=None, chunk=1024, verbose=True) # [1]

    num_iterations = int(duration / update_interval)

    print(f"開始錄音，總時長 {duration} 秒，每 {update_interval} 秒更新一次圖表...")

    for i in range(num_iterations):
        start_time_loop = time.time() # 用於確保更新間隔

        # 錄製一小段音訊
        # recorder.record_audio 的 duration 參數是秒
        single_ori = recorder.record_audio(duration=update_interval) # [1]

        # 更新音訊歷史數據
        audio_history = np.concatenate((audio_history, single_ori))
        # 保持歷史數據在設定的最大長度內
        if len(audio_history) > max_history_samples:
            audio_history = audio_history[-max_history_samples:]

        # 更新波形圖與頻譜圖 (針對當前這一小段音訊)
        process_and_plot(
            single_ori, sample_rate,
            ax_waveform=ax_waveform,
            ax_spectrum=ax_spectrum,
            show_plots=False  # 在即時模式下不額外顯示靜態圖
        ) # [3]

        # 即時更新頻譜圖 (針對累積的音訊歷史)
        # 第一次繪製頻譜圖時，可以加上 colorbar，之後更新時不再重複繪製以提高效率
        # 但為了簡化，這裡每次都重新繪製，如果有效率考量，可以調整
        plot_spectrogram(audio_history, sample_rate, ax_spectrogram, draw_colorbar=(i == 0)) # [3] 第一次畫 colorbar

        plt.tight_layout() # 自動調整子圖參數，使之適當填充整個圖像區域
        plt.pause(0.01) # 短暫暫停以允許圖形更新，0.01 是一個經驗值

        # 控制更新頻率
        elapsed_time_loop = time.time() - start_time_loop
        sleep_time = update_interval - elapsed_time_loop
        if sleep_time > 0:
            time.sleep(sleep_time)
        
        print(f"進度: {i+1}/{num_iterations}", end='\r')

    print("\n錄音結束。")

    # 錄音結束，關閉音訊串流
    recorder.close() # [1]

    # 生成最終的頻譜圖 (包含 colorbar) 並儲存數據
    # 確保 ax_spectrogram 在呼叫 plot_spectrogram 前是清空的，或者 plot_spectrogram 內部會 cla()
    print("正在生成最終頻譜圖並儲存數據...")
    spec, freqs, bins = plot_spectrogram(audio_history, sample_rate, ax_spectrogram, draw_colorbar=True) # [3]

    # 定義 NFFT 和 noverlap，應與 plot_spectrogram 中的一致
    # 在 signal_processor.py 中的 plot_spectrogram 使用的是 NFFT=256, noverlap=128
    NFFT_val = 256
    noverlap_val = 128
    
    current_time_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # 修改: 呼叫 save_spectrogram_to_csv 儲存為 CSV 格式
    csv_experiment_id = f"EXP_CSV_{current_time_str}"
    csv_filename = f'spectrogram_{current_time_str}.csv'
    try:
        save_spectrogram_to_csv(
            spec, freqs, bins, sample_rate,
            NFFT=NFFT_val, 
            noverlap=noverlap_val,
            experiment_id=csv_experiment_id,
            filename=csv_filename,
            save_power=True, # 可以選擇是否儲存功率和SNR數據
            save_snr=True
        )
    except Exception as e:
        print(f"儲存 CSV 檔案時發生錯誤: {e}")

    # 如果仍然需要儲存 TDMS 格式，可以取消以下註解
    # tdms_experiment_id = f"EXP_TDMS_{current_time_str}"
    # tdms_filename = f'spectrogram_{current_time_str}.tdms'
    # try:
    #     save_spectrogram_to_tdms(
    #         spec, freqs, bins, sample_rate,
    #         NFFT=NFFT_val,
    #         noverlap=noverlap_val,
    #         experiment_id=tdms_experiment_id,
    #         filename=tdms_filename
    #     ) # [2]
    # except Exception as e:
    #     print(f"儲存 TDMS 檔案時發生錯誤: {e}")

    plt.ioff()  # 關閉互動模式
    print(f"所有處理完成。最終圖表已顯示，數據已儲存。")
    plt.show()  # 顯示最終的圖表，直到手動關閉

if __name__ == '__main__':
    main()
