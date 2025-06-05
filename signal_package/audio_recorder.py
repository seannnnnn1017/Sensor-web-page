import pyaudio
import numpy as np
import sys
import time
import threading
import queue

class AudioRecorder:
    def __init__(self, sample_rate=22050, channels=None, chunk=1024, verbose=True):
        """
        初始化音訊錄製器，自動檢測可用的輸入設備和通道數。
        """
        self.sample_rate = sample_rate
        self.chunk = chunk
        self.verbose = verbose
        self.recording_queue = queue.Queue()
        self.stop_recording = threading.Event()
        
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
            for device_index in input_devices:
                dev_info = self.p.get_device_info_by_index(device_index)
                max_channels = dev_info['maxInputChannels']
                for ch in [1, 2]:
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

    def record_audio_with_timeout(self, duration=1, timeout=2):
        """
        帶超時機制的錄音方法
        """
        self.stop_recording.clear()
        num_chunks = int(self.sample_rate / self.chunk * duration)
        
        def recording_worker():
            try:
                temp_frames = []
                for _ in range(num_chunks):
                    if self.stop_recording.is_set():
                        break
                    try:
                        data = self.stream.read(self.chunk, exception_on_overflow=False)
                        temp_frames.append(data)
                    except Exception as e:
                        print(f"錄音過程中出錯: {e}")
                        break
                self.recording_queue.put(temp_frames)
            except Exception as e:
                print(f"錄音線程錯誤: {e}")
                self.recording_queue.put([])

        # 啟動錄音線程
        recording_thread = threading.Thread(target=recording_worker)
        recording_thread.daemon = True
        recording_thread.start()
        
        # 等待錄音完成或超時
        recording_thread.join(timeout)
        
        if recording_thread.is_alive():
            print("錄音超時，強制停止")
            self.stop_recording.set()
            recording_thread.join(0.5)
            
        # 獲取錄音數據
        try:
            frames = self.recording_queue.get_nowait()
        except queue.Empty:
            print("錄音數據獲取失敗")
            return np.zeros(int(self.sample_rate * duration), dtype=np.int16)
        
        if frames:
            audio_data = b''.join(frames)
            return np.frombuffer(audio_data, dtype=np.int16)
        else:
            return np.zeros(int(self.sample_rate * duration), dtype=np.int16)

    def record_audio(self, duration=1):
        """改進的錄音方法"""
        return self.record_audio_with_timeout(duration, timeout=duration + 1)

    def close(self):
        """關閉音訊串流並終止 pyaudio。"""
        try:
            self.stop_recording.set()
            if hasattr(self, 'stream'):
                self.stream.stop_stream()
                self.stream.close()
            if hasattr(self, 'p'):
                self.p.terminate()
        except Exception as e:
            print(f"關閉音訊串流時發生錯誤: {e}")
