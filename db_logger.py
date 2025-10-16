import pymongo
import datetime
import numpy as np

class DatabaseLogger:
    """一個專門用來處理 MongoDB 資料庫連接和寫入的類別。"""
    def __init__(self, uri="mongodb://localhost:27017/", db_name="sensor_data"):
        """初始化並連接到資料庫。"""
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        """執行資料庫連接。"""
        try:
            self.client = pymongo.MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ismaster')
            self.db = self.client[self.db_name]
            print("DatabaseLogger: MongoDB 連接成功。")
        except pymongo.errors.ConnectionFailure as e:
            self.db = None
            print(f"DatabaseLogger: MongoDB 連接失敗: {e}")

    def is_connected(self):
        """檢查是否已成功連接到資料庫。"""
        return self.db is not None

    def log_measurement(self, experiment_id, sensor_type, value, unit):
        """記錄一筆單點量測數據 (如溫度、測距)。"""
        if not self.is_connected():
            return
        
        doc = {
            'experiment_id': experiment_id,
            'timestamp': datetime.datetime.utcnow(),
            'sensor': sensor_type,
            'value': value,
            'unit': unit
        }
        try:
            self.db.measurements.insert_one(doc)
        except Exception as e:
            print(f"DatabaseLogger: 寫入 {sensor_type} 數據失敗: {e}")

    def log_spectrogram(self, experiment_id, start_time, end_time, sample_rate, nfft, noverlap, bins, freqs, spec, backup_filename=None):
        """記錄一整塊頻譜圖數據。"""
        if not self.is_connected():
            return
        
        if isinstance(bins, np.ndarray):
            bins = bins.tolist()
        if isinstance(freqs, np.ndarray):
            freqs = freqs.tolist()
        if isinstance(spec, np.ndarray):
            spec = spec.tolist()

        doc = {
            'experiment_id': experiment_id,
            'start_timestamp': start_time,
            'end_timestamp': end_time,
            'sample_rate': sample_rate,
            'nfft': nfft,
            'noverlap': noverlap,
            'time_bins_s': bins,
            'freq_bins_hz': freqs,
            'spectrogram_db': spec
            # 'backup_filename': backup_filename  # 新增欄位
        }
        try:
            self.db.spectrograms.insert_one(doc)
            print(f"DatabaseLogger: 實驗 {experiment_id} 的頻譜圖已儲存。")
        except Exception as e:
            print(f"DatabaseLogger: 儲存頻譜圖失敗: {e}")
    
    def close(self):
        """關閉資料庫連接。"""
        if self.client:
            self.client.close()
            print("DatabaseLogger: 資料庫連接已關閉。")
