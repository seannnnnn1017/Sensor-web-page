import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from audio_recorder import AudioRecorder
from signal_processor import process_and_plot, plot_spectrogram
from audio_save import save_spectrogram_to_csv
import datetime
import time
import signal
import sys
import psutil
import platform
import threading
import queue

class SoundRecordingApp:
    def __init__(self):
        self.sample_rate = 22050
        self.duration = 10
        self.update_interval = 0.1
        self.history_duration = 100
        self.recorder = None
        self.running = True
        self.audio_queue = queue.Queue(maxsize=100)
        
        # 設置信號處理器以便優雅退出
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        print("\n正在停止錄音...")
        self.running = False
        if self.recorder:
            self.recorder.close()
        sys.exit(0)
    
    def check_system_requirements(self):
        """檢查系統需求"""
        print("=== 系統環境檢查 ===")
        print(f"作業系統: {platform.system()} {platform.release()}")
        print(f"Python版本: {platform.python_version()}")
        print(f"CPU使用率: {psutil.cpu_percent()}%")
        print(f"記憶體使用率: {psutil.virtual_memory().percent}%")
        
        # 檢查音頻設備
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            device_count = p.get_device_count()
            print(f"音頻設備數量: {device_count}")
            p.terminate()
        except Exception as e:
            print(f"音頻系統檢查失敗: {e}")
            return False
        
        return True
    
    def setup_plots(self):
        """設置圖形界面"""
        try:
            # 設置matplotlib為非阻塞模式
            matplotlib.use('TkAgg')
            plt.ion()
            
            # 創建圖形窗口
            self.fig, self.ax = plt.subplots(3, 1, figsize=(10, 12))
            self.ax_waveform = self.ax[0]
            self.ax_spectrum = self.ax[1] 
            self.ax_spectrogram = self.ax[2]
            
            # 設置圖形樣式
            self.fig.suptitle('實時音頻分析', fontsize=16)
            
            # 設置圖形窗口關閉事件
            self.fig.canvas.mpl_connect('close_event', self.on_close)
            
            # 調整佈局
            plt.tight_layout()
            plt.show(block=False)
            
            # 確保窗口正確顯示
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            
        except Exception as e:
            print(f"設置圖形界面時發生錯誤: {e}")
            return False
        return True
    
    def on_close(self, event):
        """處理窗口關閉事件"""
        self.running = False
    
    def recording_thread(self):
        """錄音線程"""
        try:
            # 初始化錄音器
            self.recorder = AudioRecorder(
                sample_rate=self.sample_rate, 
                channels=None, 
                chunk=1024, 
                verbose=True
            )
            
            num_iterations = int(self.duration / self.update_interval)
            print(f"開始錄音，總時長 {self.duration} 秒，每 {self.update_interval} 秒更新一次...")
            
            for i in range(num_iterations):
                if not self.running:
                    break
                    
                try:
                    # 錄音
                    single_ori = self.recorder.record_audio_with_timeout(
                        duration=self.update_interval, 
                        timeout=self.update_interval + 0.5
                    )
                    
                    if len(single_ori) > 0:
                        # 將音頻數據放入隊列
                        try:
                            self.audio_queue.put((single_ori, i), block=False)
                        except queue.Full:
                            # 如果隊列滿了，移除最老的數據
                            try:
                                self.audio_queue.get_nowait()
                                self.audio_queue.put((single_ori, i), block=False)
                            except queue.Empty:
                                pass
                    
                    print(f"錄音進度: {i+1}/{num_iterations}", end='\r')
                    
                    # 控制錄音頻率
                    time.sleep(max(0.01, self.update_interval * 0.8))
                    
                except Exception as e:
                    print(f"錄音線程錯誤: {e}")
                    continue
                    
        except Exception as e:
            print(f"錄音線程初始化錯誤: {e}")
        finally:
            if self.recorder:
                self.recorder.close()
    
    def display_thread(self):
        """顯示線程"""
        audio_history = np.array([], dtype=np.int16)
        max_history_samples = int(self.history_duration * self.sample_rate)
        last_update = time.time()
        
        while self.running:
            try:
                # 檢查窗口是否仍然存在
                if not plt.fignum_exists(self.fig.number):
                    print("圖形窗口已關閉")
                    self.running = False
                    break
                
                # 處理音頻隊列中的數據
                audio_data_available = False
                while not self.audio_queue.empty():
                    try:
                        single_ori, iteration = self.audio_queue.get_nowait()
                        
                        # 更新音訊歷史數據
                        audio_history = np.concatenate((audio_history, single_ori))
                        if len(audio_history) > max_history_samples:
                            audio_history = audio_history[-max_history_samples:]
                        
                        audio_data_available = True
                        
                    except queue.Empty:
                        break
                
                # 控制更新頻率（每0.5秒更新一次圖形）
                current_time = time.time()
                if audio_data_available and (current_time - last_update) >= 0.5:
                    try:
                        # 使用最新的數據片段進行顯示
                        if len(audio_history) > int(self.sample_rate * self.update_interval):
                            recent_data = audio_history[-int(self.sample_rate * self.update_interval):]
                            
                            # 更新波形圖與頻譜圖
                            process_and_plot(
                                recent_data, self.sample_rate,
                                ax_waveform=self.ax_waveform,
                                ax_spectrum=self.ax_spectrum,
                                show_plots=False
                            )
                            
                            # 更新頻譜圖
                            plot_spectrogram(
                                audio_history, self.sample_rate, 
                                self.ax_spectrogram, 
                                draw_colorbar=False
                            )
                            
                            # 強制刷新顯示
                            self.fig.canvas.draw_idle()
                            self.fig.canvas.flush_events()
                            
                            last_update = current_time
                    
                    except Exception as e:
                        print(f"顯示更新錯誤: {e}")
                
                # 處理GUI事件
                try:
                    self.fig.canvas.flush_events()
                except:
                    pass
                
                # 短暫休眠以減少CPU使用率
                time.sleep(0.05)
                
            except Exception as e:
                print(f"顯示線程錯誤: {e}")
                time.sleep(0.1)
        
        # 保存最終數據
        if len(audio_history) > 0:
            self.save_final_data(audio_history)
    
    def run(self):
        """主運行方法"""
        try:
            # 檢查系統環境
            if not self.check_system_requirements():
                print("系統環境檢查失敗，請檢查依賴庫安裝")
                return
            
            # 設置圖形界面
            if not self.setup_plots():
                print("圖形界面設置失敗")
                return
            
            # 創建並啟動線程
            recording_thread = threading.Thread(target=self.recording_thread)
            display_thread = threading.Thread(target=self.display_thread)
            
            recording_thread.daemon = True
            display_thread.daemon = True
            
            recording_thread.start()
            display_thread.start()
            
            # 等待線程完成
            recording_thread.join()
            display_thread.join()
                
        except Exception as e:
            print(f"主程序錯誤: {e}")
        finally:
            self.cleanup()
    
    def save_final_data(self, audio_history):
        """保存最終數據"""
        try:
            print("\n正在生成最終頻譜圖並儲存數據...")
            
            # 檢查窗口是否仍然存在
            if plt.fignum_exists(self.fig.number):
                spec, freqs, bins = plot_spectrogram(
                    audio_history, self.sample_rate, 
                    self.ax_spectrogram, draw_colorbar=True
                )
                
                # 強制更新顯示
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()
            else:
                # 如果窗口不存在，創建臨時圖形進行計算
                temp_fig, temp_ax = plt.subplots(1, 1)
                spec, freqs, bins = plot_spectrogram(
                    audio_history, self.sample_rate, 
                    temp_ax, draw_colorbar=False
                )
                plt.close(temp_fig)
            
            # 檢查數據有效性
            if len(spec) == 0 or len(freqs) == 0 or len(bins) == 0:
                print("警告：無法生成有效的頻譜數據")
                return
            
            current_time_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_experiment_id = f"EXP_CSV_{current_time_str}"
            csv_filename = f'spectrogram_{current_time_str}.csv'
            
            save_spectrogram_to_csv(
                spec, freqs, bins, self.sample_rate,
                NFFT=256, noverlap=128,
                experiment_id=csv_experiment_id,
                filename=csv_filename,
                save_power=True,
                save_snr=True
            )
            
            print(f"數據已成功儲存到 {csv_filename}")
            
            # 顯示最終結果
            if plt.fignum_exists(self.fig.number):
                print("按任意鍵關閉圖形窗口...")
                plt.show()
            
        except Exception as e:
            print(f"儲存數據時發生錯誤: {e}")
    
    def cleanup(self):
        """清理資源"""
        print("\n清理資源...")
        self.running = False
        if self.recorder:
            self.recorder.close()
        try:
            if hasattr(self, 'fig'):
                plt.close(self.fig)
            plt.close('all')
            plt.ioff()
        except Exception as e:
            print(f"清理圖形時發生錯誤: {e}")

def main():
    app = SoundRecordingApp()
    app.run()

if __name__ == '__main__':
    main()