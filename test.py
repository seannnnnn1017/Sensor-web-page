import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import scipy.fftpack

# 音頻參數
CHUNK = 1024  # 每次讀取的樣本數
FORMAT = pyaudio.paInt16  # 16 位元格式
CHANNELS = 1  # 單聲道
RATE = 44100  # 取樣率 44.1kHz

# 初始化 PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT, channels=CHANNELS,
                rate=RATE, input=True,
                frames_per_buffer=CHUNK)

# 設置圖表
plt.ion()
fig, ax = plt.subplots()
x = np.fft.fftfreq(CHUNK, 1.0/RATE)[:CHUNK//2]  # 頻率軸
line, = ax.plot(x, np.zeros(CHUNK//2))
ax.set_xlim(0, RATE/2)
ax.set_ylim(0, 100000)  # 依實際情況調整
ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("Amplitude")
ax.set_title("Real-Time Frequency Spectrum")

try:
    while True:
        data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        fft_data = np.abs(scipy.fftpack.fft(data))[:CHUNK//2]
        line.set_ydata(fft_data)
        plt.pause(0.01)
except KeyboardInterrupt:
    print("Stopping...")
    stream.stop_stream()
    stream.close()
    p.terminate()
    plt.close()
