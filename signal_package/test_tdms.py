import numpy as np
import matplotlib as mpl
mpl.use('TkAgg')  # 避免圖形顯示問題
import matplotlib.pyplot as plt
from nptdms import TdmsFile
import os
import sys
import re
import traceback

def load_spectrogram_from_tdms(filename):
    """從TDMS檔案中加載頻譜圖數據"""
    try:
        if not os.path.exists(filename):
            raise FileNotFoundError(f"找不到檔案: {filename}")
        
        # 使用TdmsFile.read而非open方法
        tdms_file = TdmsFile.read(filename)
        
        # 讀取根屬性（元數據）
        properties = {
            'EId': tdms_file.properties.get('EId', 'Unknown'),
            'timestamp': tdms_file.properties.get('timestamp', 'Unknown'),
            'sample_rate': tdms_file.properties.get('sample_rate'),
            'NFFT': tdms_file.properties.get('NFFT'),
            'noverlap': tdms_file.properties.get('noverlap')
        }
        
        # 列出所有群組名稱
        group_names = [group.name for group in tdms_file.groups()]
        print(f"檔案中的群組: {group_names}")
        
        if not group_names:
            raise ValueError("TDMS檔案中未找到任何群組")
        
        # 嘗試找到合適的頻譜圖群組
        spectrogram_group = None
        
        # 1. 直接使用第一個群組
        spectrogram_group = tdms_file.groups()[0]
        print(f"使用群組: {spectrogram_group.name}")
        
        # 列出群組中的所有通道
        channels = list(spectrogram_group.channels())
        channel_names = [ch.name for ch in channels]
        print(f"群組中的通道: {channel_names[:5]}... (共{len(channel_names)}個)")
        
        # 尋找頻率和時間通道
        freq_channel = None
        time_channel = None
        
        for channel in channels:
            if channel.name in ['Frequencies', 'Frequency', 'frequencies']:
                freq_channel = channel
                print(f"找到頻率通道: {channel.name}")
            elif channel.name in ['Time', 'time', 'Times', 'times']:
                time_channel = channel
                print(f"找到時間通道: {channel.name}")
        
        if freq_channel is None or time_channel is None:
            raise ValueError(f"在群組 '{spectrogram_group.name}' 中未找到必要的頻率或時間通道")
        
        # 讀取頻率和時間軸
        freqs = freq_channel[:]
        bins = time_channel[:]
        
        # 計算頻譜圖形狀
        n_freqs = len(freqs)
        n_times = len(bins)
        
        print(f"頻率數量: {n_freqs}, 時間點數量: {n_times}")
        
        # 創建空的頻譜圖數據數組
        spec = np.zeros((n_freqs, n_times), dtype=np.float64)
        
        # 尋找所有頻率相關的通道
        freq_patterns = [
            re.compile(r'^Frequency_(\d+\.\d+)_Hz$'),
            re.compile(r'^dB_(\d+\.\d+)Hz$')
        ]
        
        # 讀取每個頻率通道的數據
        channels_found = 0
        for i, freq in enumerate(freqs):
            channel_found = False
            
            # 嘗試多種常見命名格式
            possible_names = [
                f'Frequency_{freq:.2f}_Hz',
                f'dB_{freq:.2f}Hz',
                f'Power_{freq:.2f}Hz'
            ]
            
            for name in possible_names:
                if name in channel_names:
                    try:
                        spec[i, :] = spectrogram_group[name][:]
                        channel_found = True
                        channels_found += 1
                        if i < 3 or i > n_freqs - 3:  # 只顯示開頭和結尾的幾個通道
                            print(f"讀取通道: {name}")
                        break
                    except Exception as e:
                        print(f"警告: 讀取通道 '{name}' 時出錯: {e}")
            
            if not channel_found:
                # 如果沒找到匹配的通道名稱，用零填充
                if i < 3 or i > n_freqs - 3:
                    print(f"找不到頻率 {freq:.2f}Hz 的通道，用零填充")
        
        print(f"成功找到並讀取 {channels_found}/{n_freqs} 個頻率通道")
        return spec, freqs, bins, properties
        
    except Exception as e:
        print(f"加載TDMS檔案時出錯: {e}")
        traceback.print_exc()
        raise

def plot_spectrogram(spec, freqs, bins, properties, save_path=None):
    """繪製頻譜圖"""
    plt.figure(figsize=(12, 8))
    
    # 使用pcolormesh繪製頻譜圖
    plt.pcolormesh(bins, freqs, spec, cmap='jet', shading='gouraud')
    
    # 設置標題和標籤
    eid = properties.get('EId', 'Unknown')
    sample_rate = properties.get('sample_rate')
    nfft = properties.get('NFFT')
    noverlap = properties.get('noverlap')
    
    title = f'重建的頻譜圖 (實驗ID: {eid})'
    if sample_rate:
        title += f'\n採樣率: {sample_rate} Hz'
        if nfft:
            title += f', NFFT: {int(nfft)}'
        if noverlap:
            title += f', 重疊: {int(noverlap)}'
    
    plt.title(title, fontsize=14)
    plt.xlabel('時間 (秒)', fontsize=12)
    plt.ylabel('頻率 (Hz)', fontsize=12)
    
    # 添加顏色條
    cbar = plt.colorbar()
    cbar.set_label('振幅 (dB)', fontsize=12)
    
    # 添加網格線以便更好地查看
    plt.grid(True, alpha=0.3)
    
    # 如果指定了保存路徑，保存圖像
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"頻譜圖已保存到 {save_path}")
    
    return plt

def analyze_tdms_structure(filename):
    """分析TDMS檔案結構並打印詳細信息"""
    try:
        if not os.path.exists(filename):
            raise FileNotFoundError(f"找不到檔案: {filename}")
            
        tdms_file = TdmsFile.read(filename)
        
        print(f"\n==== TDMS檔案結構分析 ====")
        print(f"檔案: {filename}")
        
        # 打印根屬性
        print("\n根屬性:")
        for key, value in tdms_file.properties.items():
            print(f"  {key}: {value}")
        
        # 打印所有群組
        print("\n群組:")
        groups = list(tdms_file.groups())
        for group in groups:
            print(f"- {group.name}")
            
            # 打印該群組中的通道數量
            channels = list(group.channels())
            print(f"  通道數量: {len(channels)}")
            
            # 只打印前5個通道
            if channels:
                print("  部分通道示例:")
                for i, channel in enumerate(channels[:5]):
                    print(f"    - {channel.name}")
                if len(channels) > 5:
                    print(f"    ... 以及其他 {len(channels)-5} 個通道")
        
        print("\n==== 分析完成 ====\n")
        
    except Exception as e:
        print(f"分析TDMS檔案時出錯: {e}")
        traceback.print_exc()

def main():
    """主函數"""
    # 設置matplotlib中文支持
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默認字體為黑體
    plt.rcParams['axes.unicode_minus'] = False  # 解決保存圖像是負號'-'顯示為方塊的問題
    
    # 檢查命令行參數
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = 'spectrogram.tdms'  # 默認檔案名
    
    try:
        # 分析TDMS檔案結構
        analyze_tdms_structure(filename)
        
        # 加載頻譜圖數據
        print(f"正在從 {filename} 加載頻譜圖數據...")
        spec, freqs, bins, properties = load_spectrogram_from_tdms(filename)
        
        # 繪製並顯示頻譜圖
        print("正在繪製頻譜圖...")
        save_path = os.path.splitext(filename)[0] + '_reconstructed.png'
        plt_obj = plot_spectrogram(spec, freqs, bins, properties, save_path)
        
        # 顯示圖形
        print("顯示頻譜圖，關閉窗口繼續...")
        plt_obj.show(block=True)  # 使用block=True確保圖形顯示
        
        print(f"\n成功從TDMS檔案 '{filename}' 重建頻譜圖！")
        
    except Exception as e:
        print(f"\n錯誤: {e}")
        print("請確保TDMS檔案存在且格式正確。")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
