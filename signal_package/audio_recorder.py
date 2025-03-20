import pyaudio
import numpy as np

class AudioRecorder:
    def __init__(self, sample_rate=22050, channels=1, chunk=1024, verbose=True):
        """
        初始化音訊錄製器，並僅在啟動時列出一次可用設備。
        參數：
        - sample_rate: 採樣率（Hz）
        - channels: 通道數（1 表示單聲道）
        - chunk: 每次讀取的幀數
        - verbose: 是否打印可用設備資訊（預設 True）
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.verbose = verbose
        self.p = pyaudio.PyAudio()

        if self.verbose:
            print("可用音訊設備：")
            for i in range(self.p.get_device_count()):
                dev = self.p.get_device_info_by_index(i)
                if dev['maxInputChannels'] > 0:
                    print(f"設備 {i}: {dev['name']}")
        
        # 開啟音訊串流（只開一次）
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=self.channels,
                                  rate=self.sample_rate,
                                  input=True,
                                  frames_per_buffer=self.chunk)

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
        for _ in range(num_chunks):
            data = self.stream.read(self.chunk)
            frames.append(data)
        audio_data = b''.join(frames)
        return np.frombuffer(audio_data, dtype=np.int16)

    def close(self):
        """關閉音訊串流並終止 pyaudio。"""
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
