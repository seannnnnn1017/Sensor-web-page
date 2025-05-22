# audio_save.py

from nptdms import TdmsWriter, RootObject, GroupObject, ChannelObject
import numpy as np
import datetime
import os
import traceback

def save_spectrogram_to_tdms(spec, freqs, bins, sample_rate, NFFT, noverlap, experiment_id=None, filename='spectrogram.tdms'):
    """
    將 spectrogram 數據儲存到 TDMS 檔案中。
    此函式保持不變，用於 TDMS 格式的儲存。
    """
    # 如果檔案已存在，先刪除以避免附加到損壞的檔案
    if os.path.exists(filename):
        os.remove(filename)
    # 刪除相關的索引文件
    if os.path.exists(filename + "_index"):
        os.remove(filename + "_index")

    try:
        spec = np.asarray(spec, dtype=np.float64)
        if len(spec.shape) != 2:
            raise ValueError(f"頻譜圖數據應為二維數組，但得到的形狀為: {spec.shape}")
        
        n_freqs, n_times = spec.shape

        if len(freqs) != n_freqs:
            raise ValueError(f"頻率軸長度 ({len(freqs)}) 與頻譜圖行數 ({n_freqs}) 不匹配")
        
        if len(bins) != n_times:
            raise ValueError(f"時間軸長度 ({len(bins)}) 與頻譜圖列數 ({n_times}) 不匹配")

        if experiment_id is None:
            experiment_id = f"EXP_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        timestamp = datetime.datetime.now().isoformat()
        power_data = np.power(spec, 2)
        snr_data = np.zeros_like(spec)
        for i in range(n_freqs):
            signal = spec[i, :]
            signal_max = np.max(np.abs(signal))
            noise_level = np.mean(np.abs(signal))
            if noise_level > 1e-9: # 避免除以零或極小值
                snr = 20 * np.log10(signal_max / noise_level)
                snr_data[i, :] = snr
            else:
                snr_data[i, :] = 0 # 或其他合適的預設值

        with TdmsWriter(filename, mode='w') as tdms_writer:
            root = RootObject(properties={
                'EId': experiment_id, 'timestamp': timestamp,
                'sample_rate': float(sample_rate), 'NFFT': int(NFFT), 'noverlap': int(noverlap)
            })
            tdms_writer.write_segment([root])
            group = GroupObject('Spectrogram', properties={
                'EId': experiment_id, 'timestamp': timestamp, 'description': '頻譜圖數據及相關信息'
            })
            tdms_writer.write_segment([group])
            
            eid_array = np.array([experiment_id] * n_times, dtype=object) #確保 EId 與時間點對應
            eid_channel = ChannelObject('Spectrogram', 'EId', eid_array, properties={'description': '實驗ID'})
            tdms_writer.write_segment([eid_channel])

            time_channel = ChannelObject('Spectrogram', 'Time', bins, properties={
                'minimum': np.min(bins) if n_times > 0 else 0, 
                'maximum': np.max(bins) if n_times > 0 else 0, 
                'unit_string': 's', 'description': '時間軸'
            })
            tdms_writer.write_segment([time_channel])

            freq_channel = ChannelObject('Spectrogram', 'Frequencies', freqs, properties={
                'minimum': np.min(freqs) if n_freqs > 0 else 0, 
                'maximum': np.max(freqs) if n_freqs > 0 else 0, 
                'unit_string': 'Hz', 'description': '頻率軸'
            })
            tdms_writer.write_segment([freq_channel])

            for i, freq in enumerate(freqs):
                # dB data (spec)
                db_data_ch = spec[i, :].astype(np.float64)
                db_data_ch = np.nan_to_num(db_data_ch, nan=0.0, posinf=0.0, neginf=0.0)
                db_channel = ChannelObject('Spectrogram', f'dB_{freq:.2f}Hz', db_data_ch, properties={
                    'minimum': float(np.min(db_data_ch)) if n_times > 0 else 0, 
                    'maximum': float(np.max(db_data_ch)) if n_times > 0 else 0, 
                    'unit_string': 'dB_like', 'description': f'{freq:.2f}Hz 頻率的類dB數據', 'frequency': float(freq)
                }) # Clarified unit string
                tdms_writer.write_segment([db_channel])

                # Power data
                power_data_ch = power_data[i, :].astype(np.float64)
                power_data_ch = np.nan_to_num(power_data_ch, nan=0.0, posinf=0.0, neginf=0.0)
                power_channel = ChannelObject('Spectrogram', f'Power_{freq:.2f}Hz', power_data_ch, properties={
                    'minimum': float(np.min(power_data_ch)) if n_times > 0 else 0, 
                    'maximum': float(np.max(power_data_ch)) if n_times > 0 else 0, 
                    'unit_string': 'Power_Unit', 'description': f'{freq:.2f}Hz 頻率的功率數據', 'frequency': float(freq)
                }) # Clarified unit string
                tdms_writer.write_segment([power_channel])

                # SNR data
                snr_data_ch = snr_data[i, :].astype(np.float64)
                snr_data_ch = np.nan_to_num(snr_data_ch, nan=0.0, posinf=0.0, neginf=0.0)
                snr_channel = ChannelObject('Spectrogram', f'SNR_{freq:.2f}Hz', snr_data_ch, properties={
                    'minimum': float(np.min(snr_data_ch)) if n_times > 0 else 0, 
                    'maximum': float(np.max(snr_data_ch)) if n_times > 0 else 0, 
                    'unit_string': 'dB', 'description': f'{freq:.2f}Hz 頻率的信噪比數據', 'frequency': float(freq)
                })
                tdms_writer.write_segment([snr_channel])
        print(f"成功將頻譜圖儲存到 {filename} (TDMS)")
    except Exception as e:
        print(f"保存 TDMS 文件時出錯: {str(e)}")
        traceback.print_exc()
        # raise # Re-raising might stop the main script, consider if this is desired

def save_spectrogram_to_csv(spec, freqs, bins, sample_rate, NFFT, noverlap, 
                           experiment_id=None, filename='spectrogram_data.csv'): # Default filename changed
    """
    將 spectrogram 相關數據 (dB-like, Power, SNR) 合併儲存到單一 CSV 檔案中。
    數據點將以固定的0.05秒間隔進行插值。
    """
    if os.path.exists(filename):
        os.remove(filename)
    
    try:
        spec = np.asarray(spec, dtype=np.float64)
        if len(spec.shape) != 2:
            raise ValueError(f"頻譜圖數據應為二維數組，但得到的形狀為: {spec.shape}")
        
        n_freqs, n_times_orig = spec.shape # Original number of time bins before interpolation

        if len(freqs) != n_freqs:
            raise ValueError(f"頻率軸長度 ({len(freqs)}) 與頻譜圖行數 ({n_freqs}) 不匹配")
        
        if len(bins) != n_times_orig: # Check against original bins length
            raise ValueError(f"時間軸長度 ({len(bins)}) 與頻譜圖列數 ({n_times_orig}) 不匹配")
            
        if experiment_id is None:
            experiment_id = f"EXP_CSV_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        timestamp = datetime.datetime.now().isoformat()

        # --- 時間軸插值固定間隔 0.05 秒 ---
        time_interval = 0.05
        # Handle cases with zero or one time point before interpolation attempt
        if n_times_orig == 0:
            print("警告：頻譜數據中沒有時間點，無法儲存 CSV。")
            return
        elif n_times_orig == 1:
            print(f"警告：頻譜數據中只有一個時間點 ({bins[0]:.2f}s)，將直接使用此單點數據。時間間隔設定為 {time_interval}s 僅用於元數據。")
            # No interpolation needed, use original spec and bins
            interpolated_spec = spec
            interpolated_bins = bins
            n_times_interpolated = 1
        else: # n_times_orig > 1
            original_intervals = np.diff(bins)
            current_interval_mean = np.mean(original_intervals) if len(original_intervals) > 0 else time_interval
            
            # 判斷是否需要插值：時間軸不均勻 或 平均間隔與目標間隔差異較大
            needs_interpolation = len(np.unique(np.round(original_intervals, 6))) > 1 or \
                                  abs(current_interval_mean - time_interval) > 1e-6

            if needs_interpolation:
                print(f"原始時間軸平均間隔 {current_interval_mean:.6f}s 或非均勻，將插值為 {time_interval}s 間隔。")
                total_time_span = bins[-1] - bins[0]
                if total_time_span < 0: # Should not happen with valid bins
                     raise ValueError("時間軸範圍無效 (結束時間早於開始時間)。")

                # 加一個小的 epsilon 避免浮點數精度問題導致少一個點
                num_new_points = int(round(total_time_span / time_interval)) + 1
                if num_new_points <= 0 : num_new_points = 1 # Ensure at least one point

                interpolated_bins = np.linspace(bins[0], bins[0] + time_interval * (num_new_points - 1), num_new_points)
                
                interpolated_spec = np.zeros((n_freqs, len(interpolated_bins)))
                for i in range(n_freqs):
                    interpolated_spec[i, :] = np.interp(interpolated_bins, bins, spec[i, :])
                
                n_times_interpolated = len(interpolated_bins)
                print(f"時間軸已插值，新時間點數量: {n_times_interpolated}。")
            else:
                print(f"原始時間軸已為均勻 {time_interval}s 間隔，無需插值。")
                interpolated_spec = spec
                interpolated_bins = bins
                n_times_interpolated = n_times_orig
        
        if n_times_interpolated == 0 : # Should be caught earlier, but as a safeguard
            print("錯誤：插值後沒有時間點，無法儲存。")
            return

        # --- 計算三種信號 ---
        # 1. "dB-like" data (使用插值後的頻譜數據)
        # 假設 spec 是 matplotlib.specgram 的輸出，通常是功率譜密度(PSD)或幅度譜。
        # 這裡我們遵循先前的命名，將其視為主要的 "dB-like" 數據。
        db_like_data = interpolated_spec

        # 2. "Power" data (基於 db_like_data，假設其為幅度，則功率為其平方)
        # 如果 db_like_data 已經是功率，則此計算為 power^2。用戶需根據 spec 來源理解此欄位。
        power_data = np.power(db_like_data, 2)

        # 3. "SNR" data (信噪比，基於 db_like_data)
        snr_data = np.zeros_like(db_like_data)
        for i in range(n_freqs):
            signal_at_freq = db_like_data[i, :]
            if n_times_interpolated > 0 : # Ensure there are data points to calculate max/mean
                signal_max = np.max(np.abs(signal_at_freq))
                noise_level = np.mean(np.abs(signal_at_freq))
                if noise_level > 1e-9: # 避免除以零或極小值
                    snr_val = 20 * np.log10(signal_max / noise_level) # 假設 db_like_data 是幅度類型的
                    snr_data[i, :] = snr_val
                else:
                    snr_data[i, :] = 0 # 或 np.nan，取決於後續分析需求
            else: # Should not happen if n_times_interpolated > 0
                snr_data[i, :] = 0


        # --- 準備 CSV 表頭和數據 ---
        header_parts = ["Time(s)"]
        for freq_val in freqs:
            header_parts.append(f"{freq_val:.2f}Hz_DB_like") # 標明是 dB-like
            header_parts.append(f"{freq_val:.2f}Hz_Power")   # 單位取決於 DB_like 的原始單位
            header_parts.append(f"{freq_val:.2f}Hz_SNR(dB)") # SNR 通常以 dB 表示
        full_header = ",".join(header_parts)

        # 合併數據陣列：n_times_interpolated 行, 1 (時間) + n_freqs * 3 (DB, Power, SNR) 列
        merged_csv_data = np.zeros((n_times_interpolated, 1 + n_freqs * 3))
        merged_csv_data[:, 0] = interpolated_bins # 插值後的時間軸

        for i in range(n_freqs): # 遍歷每個頻率
            col_idx_db = 1 + i * 3
            col_idx_power = 1 + i * 3 + 1
            col_idx_snr = 1 + i * 3 + 2
            
            merged_csv_data[:, col_idx_db]    = db_like_data[i, :]
            merged_csv_data[:, col_idx_power] = power_data[i, :]
            merged_csv_data[:, col_idx_snr]   = snr_data[i, :]
            
        # 保存為 CSV
        np.savetxt(filename, merged_csv_data, delimiter=",", header=full_header, comments="", fmt="%.6f")

        # --- 創建元數據檔案 ---
        metadata_filename = os.path.splitext(filename)[0] + '_metadata.txt'
        with open(metadata_filename, 'w') as f:
            f.write(f"Experiment ID: {experiment_id}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Sample Rate: {sample_rate} Hz\n")
            f.write(f"NFFT: {NFFT}\n")
            f.write(f"Noverlap: {noverlap}\n")
            f.write(f"Time Interval (after interpolation): {time_interval} seconds\n")
            f.write(f"Number of Time Bins (after interpolation): {n_times_interpolated}\n")
            f.write(f"Number of Frequency Bins: {n_freqs}\n")
            f.write(f"Data File: {filename}\n")
            f.write(f"Data Columns: Time(s), then for each frequency (DB-like, Power, SNR(dB))\n")
        
        print(f"成功將合併的頻譜數據 (DB-like, Power, SNR) 儲存到 {filename}")
        print(f"元數據已儲存到 {metadata_filename}")
    
    except Exception as e:
        print(f"保存合併的 CSV 文件時出錯: {str(e)}")
        traceback.print_exc()
        # raise # 重新拋出異常可能會中止主腳本的執行

# --- 測試代碼 ---
if __name__ == '__main__':
    # 生成一些模擬數據
    sample_rate_test = 22050
    NFFT_test = 128 # 減少頻點數量以使測試文件更小
    noverlap_test = 64
    
    # 模擬不均勻時間軸
    bins_test_orig = np.array([0.0, 0.04, 0.09, 0.15, 0.20, 0.23, 0.30, 0.34, 0.38, 0.45]) 
    n_times_test_orig = len(bins_test_orig)
    
    # 模擬頻率軸
    n_freqs_test = NFFT_test // 2 + 1 # 實際頻點數
    freqs_test = np.linspace(0, sample_rate_test / 2, n_freqs_test)
    
    # 模擬頻譜數據 (假設為幅度譜或類似dB的值)
    spec_test_orig = np.random.rand(n_freqs_test, n_times_test_orig) * 30 + 20 # 20 到 50 範圍
    
    experiment_id_test_csv = "TEST_MERGED_CSV_001"
    
    print("--- 測試 save_spectrogram_to_csv (合併數據) ---")
    try:
        save_spectrogram_to_csv(
            spec_test_orig, 
            freqs_test, 
            bins_test_orig, 
            sample_rate_test, 
            NFFT_test, 
            noverlap_test, 
            experiment_id=experiment_id_test_csv,
            filename='test_spectrogram_merged.csv'
        )
        print("測試 save_spectrogram_to_csv (合併數據) 完成。")
        print("請檢查 'test_spectrogram_merged.csv' 和 'test_spectrogram_merged_metadata.txt'")

        # 測試時間軸已經是0.05s間隔的情況
        print("\n--- 測試時間軸已為0.05s間隔的情況 (合併數據) ---")
        bins_uniform = np.arange(0, 0.5, 0.05) # 0, 0.05, ..., 0.45
        spec_uniform = np.random.rand(n_freqs_test, len(bins_uniform)) * 30 + 20
        save_spectrogram_to_csv(
            spec_uniform, 
            freqs_test, 
            bins_uniform, 
            sample_rate_test, 
            NFFT_test, 
            noverlap_test, 
            experiment_id="TEST_MERGED_CSV_002_UNIFORM",
            filename='test_spectrogram_merged_uniform.csv'
        )
        print("測試 save_spectrogram_to_csv (合併數據, 均勻時間) 完成。")

        # 測試只有一個時間點的情況
        print("\n--- 測試只有一個時間點的情況 (合併數據) ---")
        bins_single = np.array([0.1])
        spec_single = np.random.rand(n_freqs_test, 1) * 30 + 20
        save_spectrogram_to_csv(
            spec_single,
            freqs_test,
            bins_single,
            sample_rate_test,
            NFFT_test,
            noverlap_test,
            experiment_id="TEST_MERGED_CSV_003_SINGLE",
            filename='test_spectrogram_merged_single.csv'
        )
        print("測試 save_spectrogram_to_csv (合併數據, 單點時間) 完成。")
        
        # 測試沒有時間點的情況
        print("\n--- 測試沒有時間點的情況 (合併數據) ---")
        bins_empty = np.array([])
        spec_empty = np.empty((n_freqs_test, 0)) # 正確的空頻譜形狀
        save_spectrogram_to_csv(
            spec_empty,
            freqs_test, # 頻率軸仍然存在
            bins_empty,
            sample_rate_test,
            NFFT_test,
            noverlap_test,
            experiment_id="TEST_MERGED_CSV_004_EMPTY",
            filename='test_spectrogram_merged_empty.csv' # 此文件不應被創建
        )
        if not os.path.exists('test_spectrogram_merged_empty.csv'):
            print("測試 save_spectrogram_to_csv (合併數據, 空時間) 完成，CSV文件未創建 (符合預期)。")
        else:
            print("警告: 測試 save_spectrogram_to_csv (合併數據, 空時間) 時，不應創建的CSV文件被創建了。")


    except Exception as e_test:
        print(f"CSV 測試過程中發生錯誤: {e_test}")
        traceback.print_exc()

    # 確保 TDMS 儲存功能不受影響 (可選測試)
    print("\n--- 測試 save_spectrogram_to_tdms (確保原有功能) ---")
    try:
        save_spectrogram_to_tdms(
            spec_test_orig, 
            freqs_test, 
            bins_test_orig, 
            sample_rate_test, 
            NFFT_test, 
            noverlap_test, 
            experiment_id="TEST_TDMS_001_AFTER_CSV_MERGE", # 新的ID以區分
            filename='test_spectrogram_original.tdms'
        )
        print("測試 save_spectrogram_to_tdms 完成。")
    except Exception as e_tdms:
        print(f"TDMS 測試過程中發生錯誤: {e_tdms}")
        traceback.print_exc()

