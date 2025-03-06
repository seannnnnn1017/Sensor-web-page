import pyaudio
import numpy as np

def record_audio(duration=1, sample_rate=22050, channels=1, chunk=1024):
    """
    錄製麥克風音訊並返回原始信號 singel_ori。
    參數：
    - duration: 錄製時間（秒）
    - sample_rate: 採樣率（Hz）
    - channels: 通道數（1 表示單聲道）
    - chunk: 每次讀取的幀數
    """
    p = pyaudio.PyAudio()

    # 確認可用的麥克風設備
    print("可用音訊設備：")
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            print(f"設備 {i}: {dev['name']}")
    
    # 開啟音訊流，使用預設輸入設備
    stream = p.open(format=pyaudio.paInt16,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=chunk)

    print(f"開始錄製 {duration} 秒音訊...")
    frames = []
    for _ in range(0, int(sample_rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)

    # 關閉音訊流
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("錄製完成。")

    # 將錄製的數據轉換為 numpy 數組
    audio_data = b''.join(frames)
    singel_ori = np.frombuffer(audio_data, dtype=np.int16)
    return singel_ori