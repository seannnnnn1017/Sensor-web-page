from audio_recorder import record_audio
from signal_processor import process_and_plot

def main():
    # 設定參數
    sample_rate = 22050  # 採樣率
    duration = 10         # 錄製時間（秒）
    
    # 執行錄音和訊號處理
    singel_ori = record_audio(duration, sample_rate)
    process_and_plot(singel_ori, sample_rate)

if __name__ == '__main__':
    main()