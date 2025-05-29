import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import serial.tools.list_ports

# 假設這些是你的自定義模組
# from temp_py_package import continuous_read
# from signal_package import AudioRecorder, process_and_plot, plot_spectrogram, save_spectrogram_to_tdms

class SensorIntegrationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("感測器整合系統")
        self.root.geometry("800x600")
        
        # 狀態變數
        self.running = False
        self.temp_thread = None
        self.audio_thread = None
        
        self.setup_gui()
        self.refresh_com_ports()
        
    def setup_gui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 設定框架
        settings_frame = ttk.LabelFrame(main_frame, text="設定", padding="10")
        settings_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # COM端口選擇
        ttk.Label(settings_frame, text="溫度感測器 COM端口:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.com_temp_var = tk.StringVar()
        self.com_temp_combo = ttk.Combobox(settings_frame, textvariable=self.com_temp_var, width=10)
        self.com_temp_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(settings_frame, text="音訊設備:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.audio_device_var = tk.StringVar(value="預設音訊設備")
        ttk.Label(settings_frame, textvariable=self.audio_device_var).grid(row=0, column=3, padx=5)
        
        # 重新整理COM端口按鈕
        ttk.Button(settings_frame, text="重新整理", command=self.refresh_com_ports).grid(row=0, column=4, padx=5)
        
        # 執行時間設定
        ttk.Label(settings_frame, text="執行時間(秒):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.duration_var = tk.StringVar(value="60")
        duration_entry = ttk.Entry(settings_frame, textvariable=self.duration_var, width=10)
        duration_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(settings_frame, text="(-1 為無限)").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # 音訊參數設定
        audio_frame = ttk.LabelFrame(settings_frame, text="音訊參數")
        audio_frame.grid(row=2, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(audio_frame, text="採樣率:").grid(row=0, column=0, padx=5)
        self.sample_rate_var = tk.StringVar(value="22050")
        ttk.Entry(audio_frame, textvariable=self.sample_rate_var, width=8).grid(row=0, column=1, padx=5)
        
        ttk.Label(audio_frame, text="更新間隔:").grid(row=0, column=2, padx=5)
        self.update_interval_var = tk.StringVar(value="0.1")
        ttk.Entry(audio_frame, textvariable=self.update_interval_var, width=8).grid(row=0, column=3, padx=5)
        
        ttk.Label(audio_frame, text="歷史記錄時長:").grid(row=0, column=4, padx=5)
        self.history_duration_var = tk.StringVar(value="100")
        ttk.Entry(audio_frame, textvariable=self.history_duration_var, width=8).grid(row=0, column=5, padx=5)
        
        # 控制按鈕
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(control_frame, text="開始監測", command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="停止監測", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 狀態顯示
        status_frame = ttk.LabelFrame(main_frame, text="狀態顯示", padding="10")
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 溫度顯示
        self.temp_label = ttk.Label(status_frame, text="溫度: -- °C", font=("Arial", 12))
        self.temp_label.grid(row=0, column=0, sticky=tk.W, padx=10)
        
        # 執行時間顯示
        self.time_label = ttk.Label(status_frame, text="執行時間: 0 秒", font=("Arial", 10))
        self.time_label.grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        # 狀態訊息
        self.status_label = ttk.Label(status_frame, text="狀態: 待機中", font=("Arial", 10))
        self.status_label.grid(row=2, column=0, sticky=tk.W, padx=10)
        
        # 圖形顯示區域
        plot_frame = ttk.LabelFrame(main_frame, text="音訊監測", padding="5")
        plot_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 創建matplotlib圖形
        self.fig, self.axes = plt.subplots(3, 1, figsize=(10, 8))
        self.ax_waveform = self.axes[0]
        self.ax_spectrum = self.axes[1]
        self.ax_spectrogram = self.axes[2]
        
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 配置權重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
    
    def refresh_com_ports(self):
        """重新整理可用的COM端口"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.com_temp_combo['values'] = ports
        if ports:
            self.com_temp_combo.set(ports[0])
    
    def start_monitoring(self):
        """開始監測"""
        try:
            # 驗證輸入
            if not self.com_temp_var.get():
                messagebox.showerror("錯誤", "請選擇溫度感測器COM端口")
                return
            
            duration = int(self.duration_var.get())
            sample_rate = int(self.sample_rate_var.get())
            update_interval = float(self.update_interval_var.get())
            history_duration = float(self.history_duration_var.get())
            
            # 設定狀態
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="狀態: 監測中...")
            
            # 開始監測執行緒
            self.start_temperature_monitoring()
            self.start_audio_monitoring(sample_rate, update_interval, history_duration, duration)
            
        except ValueError as e:
            messagebox.showerror("錯誤", f"參數輸入錯誤: {e}")
    
    def stop_monitoring(self):
        """停止監測"""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="狀態: 已停止")
        
        # 等待執行緒結束
        if self.temp_thread and self.temp_thread.is_alive():
            self.temp_thread.join(timeout=1)
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1)
    
    def start_temperature_monitoring(self):
        """開始溫度監測執行緒"""
        def temp_worker():
            com_port = self.com_temp_var.get()
            while self.running:
                try:
                    # 這裡調用你的溫度讀取函數
                    # temp = continuous_read(com_port)
                    # 暫時用模擬數據
                    temp = 25.0 + np.random.random() * 5.0
                    
                    if temp is not None:
                        self.root.after(0, lambda: self.temp_label.config(text=f"溫度: {temp:.1f} °C"))
                    else:
                        self.root.after(0, lambda: self.temp_label.config(text="溫度: 讀取失敗"))
                        
                    time.sleep(1)  # 溫度每秒更新一次
                except Exception as e:
                    print(f"溫度讀取錯誤: {e}")
                    break
        
        self.temp_thread = threading.Thread(target=temp_worker, daemon=True)
        self.temp_thread.start()
    
    def start_audio_monitoring(self, sample_rate, update_interval, history_duration, duration):
        """開始音訊監測執行緒"""
        def audio_worker():
            try:
                # 初始化音訊相關變數
                audio_history = np.array([], dtype=np.int16)
                max_history_samples = int(history_duration * sample_rate)
                
                # 初始化錄音器
                # recorder = AudioRecorder(sample_rate=sample_rate, channels=None, chunk=1024, verbose=True)
                
                start_time = time.time()
                iteration = 0
                
                while self.running:
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    
                    # 檢查是否達到設定時間
                    if duration > 0 and elapsed_time >= duration:
                        break
                    
                    # 更新時間顯示
                    self.root.after(0, lambda t=elapsed_time: self.time_label.config(text=f"執行時間: {int(t)} 秒"))
                    
                    # 模擬音訊數據 (替代實際錄音)
                    # single_ori = recorder.record_audio(update_interval)
                    # 暫時用模擬數據
                    samples = int(sample_rate * update_interval)
                    single_ori = np.random.randint(-32768, 32767, samples, dtype=np.int16)
                    
                    audio_history = np.concatenate((audio_history, single_ori))
                    if len(audio_history) > max_history_samples:
                        audio_history = audio_history[-max_history_samples:]
                    
                    # 更新圖形 (在主執行緒中執行)
                    self.root.after(0, lambda: self.update_plots(single_ori, audio_history, sample_rate))
                    
                    time.sleep(update_interval)
                    iteration += 1
                
                # 錄音結束處理
                # recorder.close()
                
                # 儲存最終數據
                if len(audio_history) > 0:
                    self.save_final_data(audio_history, sample_rate)
                
                # 停止監測
                self.root.after(0, self.stop_monitoring)
                
            except Exception as e:
                print(f"音訊監測錯誤: {e}")
                self.root.after(0, self.stop_monitoring)
        
        self.audio_thread = threading.Thread(target=audio_worker, daemon=True)
        self.audio_thread.start()
    
    def update_plots(self, single_ori, audio_history, sample_rate):
        """更新圖形顯示"""
        try:
            # 清除前一次的圖形
            for ax in self.axes:
                ax.clear()
            
            # 繪製波形
            time_axis = np.arange(len(single_ori)) / sample_rate
            self.ax_waveform.plot(time_axis, single_ori)
            self.ax_waveform.set_title("即時波形")
            self.ax_waveform.set_xlabel("時間 (秒)")
            self.ax_waveform.set_ylabel("振幅")
            
            # 繪製頻譜
            if len(single_ori) > 0:
                fft = np.fft.rfft(single_ori)
                freqs = np.fft.rfftfreq(len(single_ori), 1/sample_rate)
                self.ax_spectrum.plot(freqs, np.abs(fft))
                self.ax_spectrum.set_title("頻譜")
                self.ax_spectrum.set_xlabel("頻率 (Hz)")
                self.ax_spectrum.set_ylabel("振幅")
                self.ax_spectrum.set_xlim(0, sample_rate/2)
            
            # 繪製頻譜圖
            if len(audio_history) > 256:  # 確保有足夠的數據
                f, t, Sxx = plt.mlab.specgram(audio_history, NFFT=256, Fs=sample_rate, noverlap=128)
                self.ax_spectrogram.imshow(10 * np.log10(Sxx), aspect='auto', origin='lower', 
                                         extent=[0, len(audio_history)/sample_rate, 0, sample_rate/2])
                self.ax_spectrogram.set_title("頻譜圖")
                self.ax_spectrogram.set_xlabel("時間 (秒)")
                self.ax_spectrogram.set_ylabel("頻率 (Hz)")
            
            self.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            print(f"圖形更新錯誤: {e}")
    
    def save_final_data(self, audio_history, sample_rate):
        """儲存最終數據"""
        try:
            experiment_id = "EXP_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'spectrogram_{experiment_id}.npz'
            
            # 計算頻譜圖
            f, t, Sxx = plt.mlab.specgram(audio_history, NFFT=256, Fs=sample_rate, noverlap=128)
            
            # 儲存為numpy格式 (替代TDMS)
            np.savez(filename, 
                    spectrogram=Sxx, 
                    frequencies=f, 
                    times=t, 
                    sample_rate=sample_rate,
                    experiment_id=experiment_id)
            
            print(f"數據已儲存至: {filename}")
            
        except Exception as e:
            print(f"數據儲存錯誤: {e}")

def main():
    root = tk.Tk()
    app = SensorIntegrationGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()