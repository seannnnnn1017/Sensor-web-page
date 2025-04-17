import pyaudio
import numpy as np
import sys
import time

class AudioRecorder:
    def __init__(self, sample_rate=22050, channels=None, chunk=1024, verbose=True):
        """
        初始化音訊錄製器，自動檢測可用的輸入設備和通道數。
        參數：
        - sample_rate: 採樣率（Hz）
        - channels: 通道數（預設為 None，自動檢測）
        - chunk: 每次讀取的幀數
        - verbose: 是否打印可用設備資訊（預設 True）
        """
        self.sample_rate = sample_rate
        self.chunk = chunk
        self.verbose = verbose
        
        try:
            self.p = pyaudio.PyAudio()
        except Exception as e:
            print(f"PyAudio 初始化錯誤: {e}")
            print("請確認已安裝 PyAudio 並檢查音訊系統")
            sys.exit(1)

        # 檢查可用的輸入設備
        input_devices = [
            i for i in range(self.p.get_device_count()) 
            if self.p.get_device_info_by_index(i)['maxInputChannels'] > 0
        ]

        if not input_devices:
            print("錯誤：找不到任何可用的音訊輸入設備")
            sys.exit(1)

        if self.verbose:
            print("可用音訊設備：")
            for i in input_devices:
                dev = self.p.get_device_info_by_index(i)
                print(f"設備 {i}: {dev['name']} (通道數: {dev['maxInputChannels']})")

        # 自動檢測通道數
        if channels is None:
            # 嘗試找到第一個有效的通道數
            for device_index in input_devices:
                dev_info = self.p.get_device_info_by_index(device_index)
                max_channels = dev_info['maxInputChannels']
                
                for ch in [1, 2]:  # 先嘗試單聲道，再嘗試立體聲
                    if ch <= max_channels:
                        try:
                            self.stream = self.p.open(
                                format=pyaudio.paInt16,
                                channels=ch,
                                rate=self.sample_rate,
                                input=True,
                                frames_per_buffer=self.chunk,
                                input_device_index=device_index
                            )
                            self.channels = ch
                            self.device_index = device_index
                            print(f"成功使用設備 {device_index}，通道數：{ch}")
                            return
                        except Exception:
                            continue
        else:
            # 如果指定了通道數，則使用指定的通道數
            self.channels = channels
            self.device_index = input_devices[0]
            try:
                self.stream = self.p.open(
                    format=pyaudio.paInt16,
                    channels=self.channels,
                    rate=self.sample_rate,
                    input=True,
                    frames_per_buffer=self.chunk,
                    input_device_index=self.device_index
                )
            except Exception as e:
                print(f"無法開啟音訊串流: {e}")
                print("可能是音訊設備被佔用或權限問題")
                sys.exit(1)

    def record_audio(self, duration=1):
        """
        錄製指定時長的音訊數據。
        參數：
        - duration: 錄製時間（秒）
        返回值：
        - 錄製的 numpy 陣列，數據類型為 np.int16
        """
        frames = []
        num_chunks = int(self.sample_rate / self.chunk * duration)
        
        max_retries = 3
        retry_delay = 1  # 重試間隔秒數

        for attempt in range(max_retries):
            try:
                for _ in range(num_chunks):
                    data = self.stream.read(self.chunk, exception_on_overflow=False)
                    frames.append(data)
                
                if frames:
                    audio_data = b''.join(frames)
                    return np.frombuffer(audio_data, dtype=np.int16)
                
            except IOError as e:
                print(f"音訊讀取錯誤（嘗試 {attempt + 1}/{max_retries}）: {e}")
                time.sleep(retry_delay)
                continue
        
        print("錄音失敗：多次嘗試後仍無法讀取音訊")
        return np.zeros(int(self.sample_rate * duration), dtype=np.int16)

    def close(self):
        """關閉音訊串流並終止 pyaudio。"""
        try:
            if hasattr(self, 'stream'):
                self.stream.stop_stream()
                self.stream.close()
            if hasattr(self, 'p'):
                self.p.terminate()
        except Exception as e:
            print(f"關閉音訊串流時發生錯誤: {e}")