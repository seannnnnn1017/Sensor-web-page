# audio_save.py

from nptdms import TdmsWriter, RootObject, GroupObject, ChannelObject
import numpy as np
import datetime
import os
import traceback

def save_spectrogram_to_tdms(spec, freqs, bins, sample_rate, NFFT, noverlap, experiment_id=None, filename='spectrogram.tdms'):
    """
    將 spectrogram 數據儲存到 TDMS 檔案中。

    參數：
    - spec: spectrogram 數據，shape 為 (n_freqs, n_times)
    - freqs: 頻率軸，shape 為 (n_freqs,)
    - bins: 時間軸，shape 為 (n_times,)
    - sample_rate: 採樣率
    - NFFT: FFT 窗口大小
    - noverlap: 重疊樣本數
    - experiment_id: 實驗ID，如未提供將自動生成
    - filename: TDMS 檔案名稱
    """
    # 如果檔案已存在，先刪除以避免附加到損壞的檔案
    if os.path.exists(filename):
        os.remove(filename)
    # 刪除相關的索引文件
    if os.path.exists(filename + "_index"):
        os.remove(filename + "_index")

    try:
        # 確保 spec 是正確形狀的 numpy 數組
        spec = np.asarray(spec, dtype=np.float64)
        # 檢查 spec 的形狀
        if len(spec.shape) != 2:
            raise ValueError(f"頻譜圖數據應為二維數組，但得到的形狀為: {spec.shape}")
        
        n_freqs, n_times = spec.shape

        if len(freqs) != n_freqs:
            raise ValueError(f"頻率軸長度 ({len(freqs)}) 與頻譜圖行數 ({n_freqs}) 不匹配")
        
        if len(bins) != n_times:
            raise ValueError(f"時間軸長度 ({len(bins)}) 與頻譜圖列數 ({n_times}) 不匹配")

        # 如果未提供實驗ID，則自動生成一個
        if experiment_id is None:
            experiment_id = f"EXP_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 獲取當前時間作為時間戳
        timestamp = datetime.datetime.now().isoformat()

        # 計算功率數據 (振幅平方)
        power_data = np.power(spec, 2)

        # 計算信噪比數據 (對每個頻率，信號強度與噪聲水平比值的dB)
        snr_data = np.zeros_like(spec)
        for i in range(n_freqs):
            signal = spec[i, :]
            # 使用簡單的估計：信號強度為最大值，噪聲水平為平均值
            signal_max = np.max(np.abs(signal))
            noise_level = np.mean(np.abs(signal))
            if noise_level > 0: # 避免除以零
                snr = 20 * np.log10(signal_max / noise_level) # dB
                snr_data[i, :] = snr
        
        with TdmsWriter(filename, mode='w') as tdms_writer:
            # 創建根對象並設置屬性
            root = RootObject(properties={
                'EId': experiment_id,
                'timestamp': timestamp,
                'sample_rate': float(sample_rate),
                'NFFT': int(NFFT),
                'noverlap': int(noverlap)
            })
            tdms_writer.write_segment([root])

            # 創建頻譜圖群組
            group = GroupObject('Spectrogram', properties={
                'EId': experiment_id,
                'timestamp': timestamp,
                'description': '頻譜圖數據及相關信息'
            })
            tdms_writer.write_segment([group])

            # 儲存實驗ID
            eid_array = np.array([experiment_id] * n_times, dtype=object)
            eid_channel = ChannelObject('Spectrogram', 'EId', eid_array, properties={
                'description': '實驗ID'
            })
            tdms_writer.write_segment([eid_channel])

            # 儲存時間軸
            time_min = np.min(bins)
            time_max = np.max(bins)
            time_channel = ChannelObject('Spectrogram', 'Time', bins, properties={
                'minimum': time_min,
                'maximum': time_max,
                'unit_string': 's',
                'description': '時間軸'
            })
            tdms_writer.write_segment([time_channel])

            # 儲存頻率軸
            freq_min = np.min(freqs)
            freq_max = np.max(freqs)
            freq_channel = ChannelObject('Spectrogram', 'Frequencies', freqs, properties={
                'minimum': freq_min,
                'maximum': freq_max,
                'unit_string': 'Hz',
                'description': '頻率軸'
            })
            tdms_writer.write_segment([freq_channel])

            # 儲存每個頻率的分貝、功率和信噪比數據
            for i, freq in enumerate(freqs):
                # 處理分貝數據
                db_channel_name = f'dB_{freq:.2f}Hz'
                db_data = spec[i, :].astype(np.float64)
                # 檢查並處理無效值
                if np.isnan(db_data).any() or np.isinf(db_data).any():
                    db_data = np.nan_to_num(db_data, nan=0.0, posinf=0.0, neginf=0.0)
                db_min = np.min(db_data)
                db_max = np.max(db_data)
                db_channel = ChannelObject('Spectrogram', db_channel_name, db_data, properties={
                    'minimum': float(db_min),
                    'maximum': float(db_max),
                    'unit_string': 'dB',
                    'description': f'{freq:.2f}Hz 頻率的分貝數據',
                    'frequency': float(freq)
                })
                tdms_writer.write_segment([db_channel])

                # 處理功率數據
                power_channel_name = f'Power_{freq:.2f}Hz'
                power_data_channel = power_data[i, :].astype(np.float64)
                # 檢查並處理無效值
                if np.isnan(power_data_channel).any() or np.isinf(power_data_channel).any():
                    power_data_channel = np.nan_to_num(power_data_channel, nan=0.0, posinf=0.0, neginf=0.0)
                power_min = np.min(power_data_channel)
                power_max = np.max(power_data_channel)
                power_channel = ChannelObject('Spectrogram', power_channel_name, power_data_channel, properties={
                    'minimum': float(power_min),
                    'maximum': float(power_max),
                    'unit_string': 'W',
                    'description': f'{freq:.2f}Hz 頻率的功率數據',
                    'frequency': float(freq)
                })
                tdms_writer.write_segment([power_channel])

                # 處理信噪比數據
                snr_channel_name = f'SNR_{freq:.2f}Hz'
                snr_data_channel = snr_data[i, :].astype(np.float64)
                # 檢查並處理無效值
                if np.isnan(snr_data_channel).any() or np.isinf(snr_data_channel).any():
                    snr_data_channel = np.nan_to_num(snr_data_channel, nan=0.0, posinf=0.0, neginf=0.0)
                snr_min = np.min(snr_data_channel)
                snr_max = np.max(snr_data_channel)
                snr_channel = ChannelObject('Spectrogram', snr_channel_name, snr_data_channel, properties={
                    'minimum': float(snr_min),
                    'maximum': float(snr_max),
                    'unit_string': 'dB',
                    'description': f'{freq:.2f}Hz 頻率的信噪比數據',
                    'frequency': float(freq)
                })
                tdms_writer.write_segment([snr_channel])

            # 兼容原有的test_tdms.py讀取邏輯，保留Frequency_*_Hz格式的通道
            for i, freq in enumerate(freqs):
                channel_name = f'Frequency_{freq:.2f}_Hz'
                channel_data = spec[i, :].astype(np.float64)
                # 檢查並處理無效值
                if np.isnan(channel_data).any() or np.isinf(channel_data).any():
                    channel_data = np.nan_to_num(channel_data, nan=0.0, posinf=0.0, neginf=0.0)
                min_val = np.min(channel_data)
                max_val = np.max(channel_data)
                channel = ChannelObject('Spectrogram', channel_name, channel_data, properties={
                    'minimum': float(min_val),
                    'maximum': float(max_val),
                    'monotony': 'Not monotone',
                    'unit_string': 'dB',
                    'description': f'{freq:.2f}Hz 頻率的分貝數據',
                    'frequency': float(freq)
                })
                tdms_writer.write_segment([channel])

        print(f"成功將頻譜圖儲存到 {filename}，包含實驗ID、時間、頻率、分貝、功率和信噪比數據")

    except Exception as e:
        print(f"保存 TDMS 文件時出錯: {str(e)}")
        traceback.print_exc()
        raise

def save_spectrogram_to_csv(spec, freqs, bins, sample_rate, NFFT, noverlap, experiment_id=None, 
                           filename='spectrogram.csv', save_power=False, save_snr=False):
    """
    將 spectrogram 數據儲存到 CSV 檔案中。
    
    參數：
    - spec: spectrogram 數據，shape 為 (n_freqs, n_times)
    - freqs: 頻率軸，shape 為 (n_freqs,)
    - bins: 時間軸，shape 為 (n_times,)
    - sample_rate: 採樣率
    - NFFT: FFT 窗口大小
    - noverlap: 重疊樣本數
    - experiment_id: 實驗ID，如未提供將自動生成
    - filename: CSV 檔案名稱
    - save_power: 是否儲存功率數據，預設為 False
    - save_snr: 是否儲存信噪比數據，預設為 False
    """
    
    # 如果檔案已存在，先刪除以避免附加到損壞的檔案
    if os.path.exists(filename):
        os.remove(filename)
    
    try:
        # 確保 spec 是正確形狀的 numpy 數組
        spec = np.asarray(spec, dtype=np.float64)
        
        # 檢查 spec 的形狀
        if len(spec.shape) != 2:
            raise ValueError(f"頻譜圖數據應為二維數組，但得到的形狀為: {spec.shape}")
        
        n_freqs, n_times = spec.shape
        
        if len(freqs) != n_freqs:
            raise ValueError(f"頻率軸長度 ({len(freqs)}) 與頻譜圖行數 ({n_freqs}) 不匹配")
        
        if len(bins) != n_times:
            raise ValueError(f"時間軸長度 ({len(bins)}) 與頻譜圖列數 ({n_times}) 不匹配")
            
        # 如果未提供實驗ID，則自動生成一個
        if experiment_id is None:
            experiment_id = f"EXP_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 獲取當前時間作為時間戳
        timestamp = datetime.datetime.now().isoformat()

        # 檢查時間間隔是否為 0.05 秒
        time_interval = 0.05
        if n_times > 1:
            # 計算原始數據點的平均時間間隔，用於插值前的參考
            original_intervals = np.diff(bins)
            if len(original_intervals) > 0: # 確保至少有兩個時間點
                current_interval_mean = np.mean(original_intervals)
            else: # 只有一個時間點，無法計算間隔
                current_interval_mean = time_interval # 假設為目標間隔

            # 只有當原始平均間隔與目標間隔顯著不同時才進行插值
            if abs(current_interval_mean - time_interval) > 1e-6 or len(np.unique(np.round(original_intervals, 6))) > 1 :
                print(f"警告：當前時間軸不均勻或平均間隔 ({current_interval_mean:.6f} 秒) 與要求的 {time_interval} 秒不同。將重新生成時間軸並插值。")
                
                # 計算總時間長度
                total_time_span = bins[-1] - bins[0]
                
                # 計算需要多少個 0.05 秒的間隔
                # 加一個小的 epsilon 避免浮點數精度問題導致少一個點
                num_new_points = int(round(total_time_span / time_interval)) + 1
                
                # 生成新的等間隔時間軸
                new_bins = np.linspace(bins[0], bins[0] + time_interval * (num_new_points - 1), num_new_points)
                
                # 對每個頻率，將數據插值到新的時間軸
                new_spec = np.zeros((n_freqs, len(new_bins)))
                for i in range(n_freqs):
                    # 使用線性插值
                    new_spec[i, :] = np.interp(new_bins, bins, spec[i, :])
                
                # 更新變數
                bins = new_bins
                spec = new_spec
                n_times = len(bins)
                print(f"時間軸已重新生成，共 {n_times} 個點，間隔 {time_interval} 秒。")
            else:
                print(f"當前時間軸已為等間隔 {time_interval} 秒，無需調整。")
        elif n_times == 1:
             print(f"只有一個時間點，無法插值。將使用原始時間點。時間間隔設為 {time_interval} 秒用於元數據。")
        else: # n_times == 0
            print("警告：沒有時間數據點，無法處理。")
            return # 如果沒有數據點，直接返回


        # 創建元數據檔案
        metadata_filename = os.path.splitext(filename)[0] + '_metadata.txt'
        with open(metadata_filename, 'w') as f:
            f.write(f"Experiment ID: {experiment_id}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Sample Rate: {sample_rate} Hz\n")
            f.write(f"NFFT: {NFFT}\n")
            f.write(f"Noverlap: {noverlap}\n")
            f.write(f"Time Interval: {time_interval} seconds\n")
            f.write(f"Number of Time Bins: {n_times}\n")
            f.write(f"Number of Frequency Bins: {n_freqs}\n")
        
        # 準備 CSV 表頭
        header = ["Time(s)"] # 修改表頭使其更清晰
        for freq_val in freqs: # 使用 freq_val 避免與外層 freqs 變量衝突
            header.append(f"{freq_val:.2f}Hz_dB") # 標明單位是dB
        
        # 準備 CSV 數據 (行為時間點，列為頻率)
        # 第一列是時間，之後是各頻率的dB值
        csv_data = np.zeros((n_times, n_freqs + 1))
        csv_data[:, 0] = bins # 時間軸
        for i in range(n_freqs):
            csv_data[:, i + 1] = spec[i, :] # 第 i 個頻率的數據
        
        # 保存為 CSV
        np.savetxt(filename, csv_data, delimiter=",", header=",".join(header), comments="", fmt="%.6f")
        
        # 如果需要，保存功率數據
        if save_power:
            power_filename = os.path.splitext(filename)[0] + '_power.csv'
            
            # 計算功率數據 (振幅平方)，確保使用插值後的 spec
            power_data_calc = np.power(spec, 2)
            
            # 準備 CSV 表頭 (功率)
            power_header = ["Time(s)"]
            for freq_val in freqs:
                power_header.append(f"{freq_val:.2f}Hz_Power")

            # 準備 CSV 數據 (功率)
            power_csv_data = np.zeros((n_times, n_freqs + 1))
            power_csv_data[:, 0] = bins # 使用插值後的時間軸
            for i in range(n_freqs):
                power_csv_data[:, i + 1] = power_data_calc[i, :]
            
            np.savetxt(power_filename, power_csv_data, delimiter=",", 
                       header=",".join(power_header), comments="", fmt="%.6f")
        
        # 如果需要，保存信噪比數據
        if save_snr:
            snr_filename = os.path.splitext(filename)[0] + '_snr.csv'
            
            # 計算信噪比數據，確保使用插值後的 spec
            snr_data_calc = np.zeros_like(spec)
            for i in range(n_freqs):
                signal_at_freq = spec[i, :] # 使用插值後的頻譜數據
                # 使用簡單的估計：信號強度為最大值，噪聲水平為平均值
                signal_max = np.max(np.abs(signal_at_freq))
                noise_level = np.mean(np.abs(signal_at_freq))
                if noise_level > 1e-9:  # 避免除以極小值或零
                    snr_val = 20 * np.log10(signal_max / noise_level)  # dB
                    snr_data_calc[i, :] = snr_val
                else:
                    snr_data_calc[i, :] = 0 # 或設為一個非常大的值，或 NaN
            
            # 準備 CSV 表頭 (SNR)
            snr_header = ["Time(s)"]
            for freq_val in freqs:
                snr_header.append(f"{freq_val:.2f}Hz_SNR(dB)")

            # 準備 CSV 數據 (SNR)
            snr_csv_data = np.zeros((n_times, n_freqs + 1))
            snr_csv_data[:, 0] = bins # 使用插值後的時間軸
            for i in range(n_freqs):
                snr_csv_data[:, i + 1] = snr_data_calc[i, :]
            
            np.savetxt(snr_filename, snr_csv_data, delimiter=",", 
                       header=",".join(snr_header), comments="", fmt="%.6f")

        print(f"成功將頻譜圖儲存到 {filename}，時間間隔為 {time_interval} 秒")
        print(f"元數據已儲存到 {metadata_filename}")
        if save_power:
            print(f"成功將功率數據儲存到 {power_filename}")
        if save_snr:
            print(f"成功將信噪比數據儲存到 {snr_filename}")
    
    except Exception as e:
        print(f"保存 CSV 文件時出錯: {str(e)}")
        traceback.print_exc()
        raise

# --- 測試代碼 ---
if __name__ == '__main__':
    # 生成一些模擬數據
    sample_rate_test = 22050
    NFFT_test = 256
    noverlap_test = 128
    
    # 模擬時間軸 (可能不均勻)
    bins_test = np.array([0.0, 0.04, 0.09, 0.15, 0.20, 0.23, 0.30, 0.34, 0.38, 0.45]) 
    n_times_test = len(bins_test)
    
    # 模擬頻率軸
    n_freqs_test = NFFT_test // 2 + 1
    freqs_test = np.linspace(0, sample_rate_test / 2, n_freqs_test)
    
    # 模擬頻譜數據 (dB)
    spec_test = np.random.rand(n_freqs_test, n_times_test) * 50 - 20 # -20 到 30 dB
    
    experiment_id_test = "TEST_CSV_001"
    
    print("測試 save_spectrogram_to_csv...")
    try:
        save_spectrogram_to_csv(
            spec_test, 
            freqs_test, 
            bins_test, 
            sample_rate_test, 
            NFFT_test, 
            noverlap_test, 
            experiment_id=experiment_id_test,
            filename='test_spectrogram.csv',
            save_power=True,
            save_snr=True
        )
        print("測試 save_spectrogram_to_csv 完成。請檢查生成的 'test_spectrogram.csv', 'test_spectrogram_metadata.txt', 'test_spectrogram_power.csv', 'test_spectrogram_snr.csv' 檔案。")
        
        # 測試時間軸已經是0.05s間隔的情況
        print("\n測試時間軸已為0.05s間隔的情況...")
        bins_test_uniform = np.arange(0, 0.5, 0.05) # 0, 0.05, 0.1, ..., 0.45
        n_times_uniform = len(bins_test_uniform)
        spec_test_uniform = np.random.rand(n_freqs_test, n_times_uniform) * 50 - 20
        save_spectrogram_to_csv(
            spec_test_uniform, 
            freqs_test, 
            bins_test_uniform, 
            sample_rate_test, 
            NFFT_test, 
            noverlap_test, 
            experiment_id="TEST_CSV_002_UNIFORM",
            filename='test_spectrogram_uniform.csv',
            save_power=False,
            save_snr=False
        )
        print("測試 save_spectrogram_to_csv (uniform time) 完成。")

        # 測試只有一個時間點的情況
        print("\n測試只有一個時間點的情況...")
        bins_single_point = np.array([0.1])
        spec_single_point = np.random.rand(n_freqs_test, 1) * 50 - 20
        save_spectrogram_to_csv(
            spec_single_point,
            freqs_test,
            bins_single_point,
            sample_rate_test,
            NFFT_test,
            noverlap_test,
            experiment_id="TEST_CSV_003_SINGLE",
            filename='test_spectrogram_single.csv'
        )
        print("測試 save_spectrogram_to_csv (single point) 完成。")

    except Exception as e_test:
        print(f"測試過程中發生錯誤: {e_test}")
        traceback.print_exc()

    # 測試 save_spectrogram_to_tdms (確保原有功能未損壞)
    # 注意：TDMS 的 bins 數據通常是 specgram 函數直接返回的，其間隔由 NFFT 和 noverlap 決定
    # 這裡的 bins_test 僅為模擬，實際使用中 bins 應該與 spec 維度對應
    print("\n測試 save_spectrogram_to_tdms...")
    try:
        # 為了TDMS測試，我們需要一個與 spec_test 維度匹配的 bins
        # spec_test 是 (n_freqs_test, n_times_test)
        # bins_test 應該是長度為 n_times_test
        # freqs_test 應該是長度為 n_freqs_test
        save_spectrogram_to_tdms(
            spec_test, 
            freqs_test, 
            bins_test, # 使用原始的 bins_test，因為 TDMS 儲存原始數據
            sample_rate_test, 
            NFFT_test, 
            noverlap_test, 
            experiment_id="TEST_TDMS_001",
            filename='test_spectrogram.tdms'
        )
        print("測試 save_spectrogram_to_tdms 完成。請檢查生成的 'test_spectrogram.tdms' 檔案。")
    except Exception as e_tdms:
        print(f"TDMS 測試過程中發生錯誤: {e_tdms}")
        traceback.print_exc()
