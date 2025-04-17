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
    from nptdms import TdmsWriter, RootObject, GroupObject, ChannelObject
    import numpy as np
    import datetime
    import os

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
            if noise_level > 0:  # 避免除以零
                snr = 20 * np.log10(signal_max / noise_level)  # dB
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
        import traceback
        traceback.print_exc()
        raise
