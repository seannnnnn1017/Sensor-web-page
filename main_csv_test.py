import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import serial.tools.list_ports
import pyaudio
from rangefinder import LKIF2Device
from rangefinder.constants import RC_OK, LKIF_ABLEMODE_AUTO

# 導入你的自定義模組
from temp_py_package import continuous_read
from signal_package import AudioRecorder, process_and_plot, plot_spectrogram, save_spectrogram_to_tdms

class SensorIntegrationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("感測器整合系統")
        self.root.geometry("900x700")
        
        # 狀態變數
        self.running = False
        self.temp_thread = None
        self.audio_thread = None
        self.audio_recorder = None
        self.audio_history = np.array([], dtype=np.int16)
        self.colorbar_added = False
        
        # 音訊設備列表
        self.audio_devices = []
        
        self.setup_gui()
        self.refresh_com_ports()
        self.refresh_audio_devices()
        
        # 測距儀相關變數
        self.rangefinder_device = None
        self.rangefinder_thread = None
        self.distance_data = []  # 儲存距離數據
        self.temperature_data = []   # ← 放在 self.distance_data 之後

        # 測距儀參數
        self.BASIC_REF = 50.0
        self.OUT_NO = 0
        self.SAMPLING_US = 1000
        self.RANGE_CODE = 0
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
        self.com_temp_combo = ttk.Combobox(settings_frame, textvariable=self.com_temp_var, width=12)
        self.com_temp_combo.grid(row=0, column=1, padx=5)
        
        # 音訊設備選擇
        ttk.Label(settings_frame, text="音訊設備:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.audio_device_var = tk.StringVar()
        self.audio_device_combo = ttk.Combobox(settings_frame, textvariable=self.audio_device_var, width=25)
        self.audio_device_combo.grid(row=0, column=3, padx=5)
        
        # 重新整理按鈕
        refresh_frame = ttk.Frame(settings_frame)
        refresh_frame.grid(row=0, column=4, padx=5)
        ttk.Button(refresh_frame, text="重新整理COM", command=self.refresh_com_ports).pack(pady=1)
        ttk.Button(refresh_frame, text="重新整理音訊", command=self.refresh_audio_devices).pack(pady=1)
        
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
        
        self.fig, self.axes = plt.subplots(3, 1, figsize=(10, 10), 
                                        gridspec_kw={'height_ratios': [2, 2, 2]})
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
        
        # 測距儀設定（在音訊設備選擇後面加入）
        ttk.Label(settings_frame, text="測距儀模式:").grid(row=0, column=5, sticky=tk.W, padx=5)
        self.refl_mode_var = tk.StringVar(value="0")
        refl_combo = ttk.Combobox(settings_frame, textvariable=self.refl_mode_var, 
                                values=["0-漫反射", "1-鏡面反射"], width=12)
        refl_combo.grid(row=0, column=6, padx=5)
        
        # 測距儀間隔設定（在執行時間設定下面加入）
        ttk.Label(settings_frame, text="測距間隔(秒):").grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        self.distance_interval_var = tk.StringVar(value="0.1")
        distance_entry = ttk.Entry(settings_frame, textvariable=self.distance_interval_var, width=10)
        distance_entry.grid(row=1, column=4, padx=5, pady=5)

        # 距離顯示（在溫度顯示後面）
        self.distance_label = ttk.Label(status_frame, text="距離: -- mm", font=("Arial", 12))
        self.distance_label.grid(row=0, column=1, sticky=tk.W, padx=10)
    def refresh_com_ports(self):
        """重新整理可用的COM端口"""
        try:
            ports = [port.device for port in serial.tools.list_ports.comports()]
            self.com_temp_combo['values'] = ports
            if ports:
                self.com_temp_combo.set(ports[0])
            else:
                self.com_temp_combo.set("")
        except Exception as e:
            print(f"刷新COM端口錯誤: {e}")
    
    def refresh_audio_devices(self):
        """重新整理可用的音訊設備"""
        try:
            p = pyaudio.PyAudio()
            self.audio_devices = []
            device_names = []
            
            for i in range(p.get_device_count()):
                device_info = p.get_device_info_by_index(i)
                # 只顯示有輸入通道的設備（麥克風）
                if device_info['maxInputChannels'] > 0:
                    device_name = f"{i}: {device_info['name']}"
                    self.audio_devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'display_name': device_name,
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': device_info['defaultSampleRate']
                    })
                    device_names.append(device_name)
            
            p.terminate()
            
            self.audio_device_combo['values'] = device_names
            if device_names:
                # 預設選擇第一個設備
                self.audio_device_combo.set(device_names[0])
            else:
                self.audio_device_combo.set("無可用音訊設備")
                
        except Exception as e:
            print(f"刷新音訊設備錯誤: {e}")
            self.audio_device_combo['values'] = ["音訊設備檢測失敗"]
            self.audio_device_combo.set("音訊設備檢測失敗")
    
    def get_selected_audio_device_index(self):
        """取得選中的音訊設備索引"""
        selected = self.audio_device_var.get()
        if not selected or selected == "無可用音訊設備" or selected == "音訊設備檢測失敗":
            return None
        
        # 從顯示名稱中提取設備索引
        try:
            device_index = int(selected.split(':')[0])
            return device_index
        except:
            return None
    
    def start_monitoring(self):
        """開始監測"""
        try:
            # 檢查感測器狀態並收集警告訊息
            warnings = []
            temp_enabled = True
            audio_enabled = True
            rangefinder_enabled = True
            
            # 檢查溫度感測器
            if not self.com_temp_var.get():
                warnings.append("• 未選擇溫度感測器COM端口，溫度監測將被停用")
                temp_enabled = False
            
            # 檢查音訊設備
            if not self.audio_device_var.get() or self.audio_device_var.get() in ["無可用音訊設備", "音訊設備檢測失敗"]:
                warnings.append("• 未選擇有效的音訊設備，音訊監測將被停用")
                audio_enabled = False
            # 檢查測距儀
            try:
                test_device = LKIF2Device()
                rc = test_device.open()
                if rc != RC_OK:
                    warnings.append("• 測距儀連接失敗，距離監測將被停用")
                    rangefinder_enabled = False
                test_device.close()
            except Exception:
                warnings.append("• 測距儀初始化失敗，距離監測將被停用")
                rangefinder_enabled = False
            
            # 如果三個感測器都無效，則不允許啟動
            if not temp_enabled and not audio_enabled and not rangefinder_enabled:
                messagebox.showerror("錯誤", "至少需要啟用一個感測器才能開始監測")
                return
            
            # 如果有警告，顯示給用戶並詢問是否繼續
            if warnings:
                warning_msg = "檢測到以下問題：\n\n" + "\n".join(warnings) + "\n\n是否繼續執行監測？"
                if not messagebox.askyesno("警告", warning_msg):
                    return
            
            # 驗證其他參數
            duration = int(self.duration_var.get())
            sample_rate = int(self.sample_rate_var.get())
            update_interval = float(self.update_interval_var.get())
            history_duration = float(self.history_duration_var.get())
            # 新增測距儀參數驗證
            distance_interval = float(self.distance_interval_var.get())
            refl_mode = int(self.refl_mode_var.get().split('-')[0])
            
            # 設定狀態
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            # 更新狀態顯示
            status_parts = []
            if temp_enabled: status_parts.append("溫度")
            if audio_enabled: status_parts.append("音訊")
            if rangefinder_enabled: status_parts.append("距離")
            
            if status_parts:
                self.status_label.config(text=f"狀態: 監測中 ({'+'.join(status_parts)})")
            # 開始監測執行緒
            
            if temp_enabled:
                self.start_temperature_monitoring()
            else:
                self.temp_label.config(text="溫度: 未啟用")
            if audio_enabled:
                self.start_audio_monitoring(sample_rate, update_interval, history_duration, duration)
            else:
                # 如果音訊監測未啟用，仍需要處理執行時間
                self.start_timer_only(duration)
            if rangefinder_enabled:  # 新增
                self.start_rangefinder_monitoring(distance_interval, refl_mode)
            else:
                self.distance_label.config(text="距離: 未啟用")
            
        except ValueError as e:
            messagebox.showerror("錯誤", f"參數輸入錯誤: {e}")
        except Exception as e:
            messagebox.showerror("錯誤", f"啟動監測失敗: {e}")
    
    def stop_monitoring(self):
        """停止監測"""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="狀態: 已停止")
        
        # 關閉音訊錄音器
        if self.audio_recorder:
            try:
                self.audio_recorder.close()
            except:
                pass
            self.audio_recorder = None
        
        # 關閉測距儀（新增）
        if self.rangefinder_device:
            try:
                self.rangefinder_device.close()
            except:
                pass
            self.rangefinder_device = None
        
        # 等待執行緒結束
        if self.temp_thread and self.temp_thread.is_alive():
            self.temp_thread.join(timeout=1)
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1)
        if self.rangefinder_thread and self.rangefinder_thread.is_alive():  # 新增
            self.rangefinder_thread.join(timeout=1)

    
    def start_temperature_monitoring(self):
        """開始溫度監測執行緒"""
        def temp_worker():
            com_port = self.com_temp_var.get()
            consecutive_failures = 0
            max_failures = 10  # 增加容錯次數
            sensor_disconnected = False
            
            while self.running:
                try:
                    # 使用你的實際溫度讀取函數
                    temp = continuous_read(com_port)
                    
                    if temp is not None:
                        consecutive_failures = 0  # 重置失敗計數
                        current_time = time.time()                       # 新增
                        self.temperature_data.append({                   # 新增
                            'timestamp': current_time,                   # 新增
                            'temp': temp                                 # 新增
                        })                                               # 新增

                        if sensor_disconnected:
                            # 感測器重新連接成功
                            self.root.after(0, lambda: messagebox.showinfo("通知", "溫度感測器已重新連接"))
                            sensor_disconnected = False
                        self.root.after(0, lambda t=temp: self.temp_label.config(text=f"溫度: {t:.1f} °C"))
                    else:
                        consecutive_failures += 1
                        self.root.after(0, lambda: self.temp_label.config(text="溫度: 讀取失敗"))
                        
                        # 如果連續失敗達到上限，標記為斷線但繼續運行
                        if consecutive_failures >= max_failures and not sensor_disconnected:
                            sensor_disconnected = True
                            self.root.after(0, lambda: messagebox.showwarning("警告", 
                                f"溫度感測器可能已斷線，監測將繼續但不會讀取溫度數據"))
                            self.root.after(0, lambda: self.temp_label.config(text="溫度: 感測器斷線"))
                            
                    time.sleep(1)  # 溫度每秒更新一次
                    
                except Exception as e:
                    print(f"溫度讀取錯誤: {e}")
                    consecutive_failures += 1
                    self.root.after(0, lambda: self.temp_label.config(text="溫度: 連接錯誤"))
                    
                    # 只在第一次出現錯誤時提示，之後繼續運行
                    if consecutive_failures == max_failures and not sensor_disconnected:
                        sensor_disconnected = True
                        self.root.after(0, lambda err=str(e): messagebox.showwarning("警告", 
                            f"溫度感測器錯誤: {err}\n監測將繼續但不會讀取溫度數據"))
                    
                    time.sleep(1)
        
        self.temp_thread = threading.Thread(target=temp_worker, daemon=True)
        self.temp_thread.start()
    
    def start_audio_monitoring(self, sample_rate, update_interval, history_duration, duration):
        """開始音訊監測執行緒"""
        def audio_worker():
            try:
                # 初始化音訊相關變數
                self.audio_history = np.array([], dtype=np.int16)
                max_history_samples = int(history_duration * sample_rate)
                
                # 取得選中的音訊設備索引
                device_index = self.get_selected_audio_device_index()
                if device_index is None:
                    raise Exception("無效的音訊設備")
                
                # 初始化錄音器，指定設備索引
                self.audio_recorder = AudioRecorder(
                    sample_rate=sample_rate, 
                    channels=None, 
                    chunk=1024, 
                    verbose=True,
                    #device_index=device_index  # 傳入設備索引
                )
                
                start_time = time.time()
                iteration = 0
                audio_error_notified = False
                
                while self.running:
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    
                    # 檢查是否達到設定時間
                    if duration > 0 and elapsed_time >= duration:
                        break
                    
                    # 更新時間顯示
                    self.root.after(0, lambda t=elapsed_time: self.time_label.config(text=f"執行時間: {int(t)} 秒"))
                    
                    try:
                        # 錄製音訊數據
                        single_ori = self.audio_recorder.record_audio(update_interval)
                        
                        if single_ori is not None and len(single_ori) > 0:
                            self.audio_history = np.concatenate((self.audio_history, single_ori))
                            if len(self.audio_history) > max_history_samples:
                                self.audio_history = self.audio_history[-max_history_samples:]
                            
                            # 更新圖形 (在主執行緒中執行)
                            self.root.after(0, lambda s=single_ori.copy(), h=self.audio_history.copy(): 
                                          self.update_plots_with_signal_package(s, h, sample_rate))
                        
                        # 重置錯誤通知標誌
                        if audio_error_notified:
                            audio_error_notified = False
                            self.root.after(0, lambda: messagebox.showinfo("通知", "音訊設備已恢復正常"))
                            
                    except Exception as audio_error:
                        print(f"音訊錄製錯誤: {audio_error}")
                        
                        # 只在第一次出現錯誤時通知用戶
                        if not audio_error_notified:
                            audio_error_notified = True
                            self.root.after(0, lambda err=str(audio_error): messagebox.showwarning("警告", 
                                f"音訊錄製出現錯誤: {err}\n監測將繼續但音訊數據可能不完整"))
                    
                    iteration += 1
                
                # 錄音結束處理
                if self.audio_recorder:
                    self.audio_recorder.close()
                    self.audio_recorder = None
                
                # 儲存最終數據
                if len(self.audio_history) > 0:
                    self.save_final_data_with_signal_package(self.audio_history, sample_rate)
                else:
                    self.root.after(0, lambda: messagebox.showwarning("警告", "沒有錄製到音訊數據"))
                
                # 停止監測
                self.root.after(0, self.stop_monitoring)
                
            except Exception as e:
                print(f"音訊監測錯誤: {e}")
                self.root.after(0, lambda: messagebox.showwarning("警告", 
                    f"音訊監測出現問題: {e}\n監測將繼續但不會有音訊數據"))
                
                # 如果音訊失敗，仍需要處理執行時間
                self.start_timer_only(duration)
        
        self.audio_thread = threading.Thread(target=audio_worker, daemon=True)
        self.audio_thread.start()
    
    def start_rangefinder_monitoring(self, interval, refl_mode):
        """開始測距儀監測執行緒"""
        def rangefinder_worker():
            try:
                self.rangefinder_device = LKIF2Device()
                rc = self.rangefinder_device.open()
                if rc != RC_OK:
                    raise RuntimeError(f"測距儀開啟失敗: 0x{rc:X}")
                
                # 初始化感測器
                self.initialize_rangefinder()
                
                # 參數設定
                self.rangefinder_device.stop_measure()
                self.rangefinder_device.dll.LKIF2_SetSamplingCycle(self.OUT_NO, self.SAMPLING_US)
                self.rangefinder_device.dll.LKIF2_SetRange(self.OUT_NO, self.RANGE_CODE)
                self.rangefinder_device.dll.LKIF2_SetReflectionMode(self.OUT_NO, refl_mode)
                self.rangefinder_device.dll.LKIF2_SetBasicPoint(self.OUT_NO, 0)
                self.rangefinder_device.start_measure()
                
                consecutive_failures = 0
                max_failures = 10
                sensor_disconnected = False
                
                while self.running:
                    try:
                        d = self.rangefinder_device.read_single(self.OUT_NO)
                        if d['FloatResult'] == 'VALID':
                            rel_distance = d['Value']
                            abs_distance = self.BASIC_REF + rel_distance
                            
                            # 儲存數據
                            current_time = time.time()
                            self.distance_data.append({
                                'timestamp': current_time,
                                'absolute': abs_distance,
                                'relative': rel_distance
                            })
                            
                            consecutive_failures = 0
                            if sensor_disconnected:
                                self.root.after(0, lambda: messagebox.showinfo("通知", "測距儀已重新連接"))
                                sensor_disconnected = False
                            
                            self.root.after(0, lambda d=abs_distance: 
                                        self.distance_label.config(text=f"距離: {d:.1f} mm"))
                        else:
                            consecutive_failures += 1
                            self.root.after(0, lambda: self.distance_label.config(text="距離: 讀取失敗"))
                            
                            if consecutive_failures >= max_failures and not sensor_disconnected:
                                sensor_disconnected = True
                                self.root.after(0, lambda: messagebox.showwarning("警告", 
                                    "測距儀可能已斷線，監測將繼續但不會讀取距離數據"))
                                self.root.after(0, lambda: self.distance_label.config(text="距離: 感測器斷線"))
                        
                        time.sleep(interval)
                        
                    except Exception as e:
                        print(f"測距儀讀取錯誤: {e}")
                        consecutive_failures += 1
                        self.root.after(0, lambda: self.distance_label.config(text="距離: 連接錯誤"))
                        
                        if consecutive_failures == max_failures and not sensor_disconnected:
                            sensor_disconnected = True
                            self.root.after(0, lambda err=str(e): messagebox.showwarning("警告", 
                                f"測距儀錯誤: {err}\n監測將繼續但不會讀取距離數據"))
                        
                        time.sleep(interval)
                        
            except Exception as e:
                print(f"測距儀監測錯誤: {e}")
                self.root.after(0, lambda: messagebox.showwarning("警告", 
                    f"測距儀監測出現問題: {e}\n監測將繼續但不會有距離數據"))
            finally:
                if self.rangefinder_device:
                    try:
                        self.rangefinder_device.close()
                    except:
                        pass
                    self.rangefinder_device = None
        
        self.rangefinder_thread = threading.Thread(target=rangefinder_worker, daemon=True)
        self.rangefinder_thread.start()
    
    def initialize_rangefinder(self):
        """初始化測距儀"""
        self.rangefinder_device.stop_measure()
        print(">>> 測距儀 ABLE 校正中...")
        self.rangefinder_device.dll.LKIF2_SetAbleMode(self.OUT_NO, LKIF_ABLEMODE_AUTO)
        self.rangefinder_device.dll.LKIF2_AbleStart(self.OUT_NO)
        time.sleep(2)  # 自動等待2秒
        self.rangefinder_device.dll.LKIF2_AbleStop()
        print(">>> 測距儀 Auto-zero")
        self.rangefinder_device.stop_measure()
        self.rangefinder_device.dll.LKIF2_SetZeroSingle(self.OUT_NO, 1)
        print(">>> 測距儀初始化完成")

    def start_timer_only(self, duration):
        """僅啟動計時器（當音訊監測未啟用時）"""
        def timer_worker():
            start_time = time.time()
            
            while self.running:
                current_time = time.time()
                elapsed_time = current_time - start_time
                
                # 檢查是否達到設定時間
                if duration > 0 and elapsed_time >= duration:
                    self.root.after(0, self.stop_monitoring)
                    break
                
                # 更新時間顯示
                self.root.after(0, lambda t=elapsed_time: self.time_label.config(text=f"執行時間: {int(t)} 秒"))
                
                time.sleep(0.1)  # 每0.1秒更新一次時間
        
        timer_thread = threading.Thread(target=timer_worker, daemon=True)
        timer_thread.start()
    
    def update_plots_with_signal_package(self, single_ori, audio_history, sample_rate):
        """使用signal_package更新圖形顯示"""
        try:
            # 使用你的signal_package來更新波形與頻譜圖
            process_and_plot(
                single_ori, sample_rate,
                ax_waveform=self.ax_waveform,
                ax_spectrum=self.ax_spectrum,
                show_plots=False
            )
            
            # 即時更新頻譜圖，但不加 colorbar (避免重複添加)
            plot_spectrogram(audio_history, sample_rate, self.ax_spectrogram, draw_colorbar=False)
            
            # 更新畫布
            self.canvas.draw()
            
        except Exception as e:
            print(f"圖形更新錯誤: {e}")
            # 如果signal_package函數出錯，使用備用的基本繪圖
            self.update_plots_basic(single_ori, audio_history, sample_rate)
    
    def update_plots_basic(self, single_ori, audio_history, sample_rate):
        """基本圖形更新（備用方法）"""
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
            print(f"基本圖形更新錯誤: {e}")
    
    def save_final_data_with_signal_package(self, audio_history, sample_rate):
        """使用signal_package儲存最終數據"""
        try:
            experiment_id = "EXP_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 生成最終頻譜圖並儲存數據
            spec, freqs, bins = plot_spectrogram(audio_history, sample_rate, self.ax_spectrogram, draw_colorbar=True)
            save_spectrogram_to_tdms(spec, freqs, bins, sample_rate, NFFT=256, noverlap=128, 
                                 experiment_id=experiment_id,
                                 filename=f'spectrogram_{experiment_id}.tdms')
            
            print(f"數據已儲存至: spectrogram_{experiment_id}.tdms")
            
            # 更新最終顯示
            self.canvas.draw()
            
            # 顯示完成訊息
            self.root.after(0, lambda: messagebox.showinfo("完成", 
                f"監測完成！\n數據已儲存至: spectrogram_{experiment_id}.tdms"))
            
            if self.distance_data:
                distance_filename = f'distance_{experiment_id}.csv'
                with open(distance_filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Timestamp', 'Elapsed(s)', 'Absolute(mm)', 'Relative(mm)'])
                    start_time = self.distance_data[0]['timestamp'] if self.distance_data else time.time()
                    for data in self.distance_data:
                        elapsed = data['timestamp'] - start_time
                        writer.writerow([
                            data['timestamp'], 
                            f"{elapsed:.3f}", 
                            f"{data['absolute']:.3f}", 
                            f"{data['relative']:.3f}"
                        ])
                print(f"距離數據已儲存至: {distance_filename}")
            
            if self.temperature_data:
                temp_filename = f'temperature_{experiment_id}.csv'
                with open(temp_filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Timestamp', 'Elapsed(s)', 'Temperature(C)'])
                    start_time = self.temperature_data[0]['timestamp']
                    for entry in self.temperature_data:
                        elapsed = entry['timestamp'] - start_time
                        writer.writerow([
                            entry['timestamp'],
                            f"{elapsed:.3f}",
                            f"{entry['temp']:.2f}"
                        ])
                print(f"溫度數據已儲存至: {temp_filename}")

                        
        except Exception as e:
            print(f"使用signal_package儲存數據錯誤: {e}")
            self.root.after(0, lambda: messagebox.showwarning("警告", 
                f"數據儲存失敗: {e}"))

def main():
    try:
        root = tk.Tk()
        app = SensorIntegrationGUI(root)
        
        # 設定視窗關閉事件
        def on_closing():
            if app.running:
                app.stop_monitoring()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
        
    except Exception as e:
        print(f"程式啟動錯誤: {e}")
        messagebox.showerror("錯誤", f"程式啟動失敗: {e}")

if __name__ == '__main__':
    main()