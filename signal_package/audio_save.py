import numpy as np
import datetime
import os
import traceback

def save_spectrogram_to_csv(spec, freqs, bins, sample_rate, NFFT, noverlap,
                            experiment_id=None, filename='spectrogram_data.csv',
                            save_power=True, save_snr=True):
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

        n_freqs, n_times_orig = spec.shape

        if len(freqs) != n_freqs:
            raise ValueError(f"頻率軸長度 ({len(freqs)}) 與頻譜圖行數 ({n_freqs}) 不匹配")

        if len(bins) != n_times_orig:
            raise ValueError(f"時間軸長度 ({len(bins)}) 與頻譜圖列數 ({n_times_orig}) 不匹配")

        if experiment_id is None:
            experiment_id = f"EXP_CSV_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        timestamp = datetime.datetime.now().isoformat()

        # --- 時間軸插值固定間隔 0.05 秒 ---
        time_interval = 0.05

        if n_times_orig == 0:
            print("警告：頻譜數據中沒有時間點，無法儲存 CSV。")
            return
        elif n_times_orig == 1:
            interpolated_spec = spec
            interpolated_bins = bins
            n_times_interpolated = 1
        else:
            original_intervals = np.diff(bins)
            current_interval_mean = np.mean(original_intervals) if len(original_intervals) > 0 else time_interval
            needs_interpolation = len(np.unique(np.round(original_intervals, 6))) > 1 or \
                                abs(current_interval_mean - time_interval) > 1e-6

            if needs_interpolation:
                print(f"原始時間軸平均間隔 {current_interval_mean:.6f}s 或非均勻，將插值為 {time_interval}s 間隔。")
                total_time_span = bins[-1] - bins[0]
                if total_time_span < 0:
                    raise ValueError("時間軸範圍無效 (結束時間早於開始時間)。")
                
                num_new_points = int(round(total_time_span / time_interval)) + 1
                if num_new_points <= 0:
                    num_new_points = 1
                
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

        if n_times_interpolated == 0:
            print("錯誤：插值後沒有時間點，無法儲存。")
            return

        # --- 計算三種信號 ---
        db_like_data = interpolated_spec

        # 條件性計算功率和SNR數據
        power_data = None
        if save_power:
            power_data = np.power(db_like_data, 2)

        snr_data = None
        if save_snr:
            snr_data = np.zeros_like(db_like_data)
            for i in range(n_freqs):
                signal_at_freq = db_like_data[i, :]
                if n_times_interpolated > 0:
                    signal_max = np.max(np.abs(signal_at_freq))
                    noise_level = np.mean(np.abs(signal_at_freq))
                    if noise_level > 1e-9:
                        snr_val = 20 * np.log10(signal_max / noise_level)
                        snr_data[i, :] = snr_val
                    else:
                        snr_data[i, :] = 0
                else:
                    snr_data[i, :] = 0

        # --- 準備 CSV 表頭和數據 ---
        header_parts = ["Time(s)"]
        for freq_val in freqs:
            header_parts.append(f"{freq_val:.2f}Hz_DB_like")
            if save_power:
                header_parts.append(f"{freq_val:.2f}Hz_Power")
            if save_snr:
                header_parts.append(f"{freq_val:.2f}Hz_SNR(dB)")

        full_header = ",".join(header_parts)

        # 計算列數
        cols_per_freq = 1 + (1 if save_power else 0) + (1 if save_snr else 0)
        n_cols = 1 + n_freqs * cols_per_freq
        merged_csv_data = np.zeros((n_times_interpolated, n_cols))
        merged_csv_data[:, 0] = interpolated_bins

        for i in range(n_freqs):
            col_idx = 1 + i * cols_per_freq
            
            # DB-like 數據
            merged_csv_data[:, col_idx] = db_like_data[i, :]
            
            # 功率數據（如果啟用）
            if save_power:
                merged_csv_data[:, col_idx + 1] = power_data[i, :]
            
            # SNR數據（如果啟用）
            if save_snr:
                snr_col_idx = col_idx + 1 + (1 if save_power else 0)
                merged_csv_data[:, snr_col_idx] = snr_data[i, :]

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
            f.write(f"Data Columns: Time(s), then for each frequency (DB-like")
            if save_power:
                f.write(", Power")
            if save_snr:
                f.write(", SNR(dB)")
            f.write(")\n")

        success_msg = f"成功將合併的頻譜數據 (DB-like"
        if save_power:
            success_msg += ", Power"
        if save_snr:
            success_msg += ", SNR"
        success_msg += f") 儲存到 {filename}"
        
        print(success_msg)
        print(f"元數據已儲存到 {metadata_filename}")

    except Exception as e:
        print(f"保存合併的 CSV 文件時出錯: {str(e)}")
        traceback.print_exc()
