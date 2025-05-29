# spectrometer.py
# 此模組定義 Spectrometer 類別，負責統整光譜儀的初始化、測量、資料接收與關閉流程
from PyQt5.QtCore import pyqtSlot
from .interface import AvantesInterface
from .config import SpectrometerConfig
from .calibration import apply_calibration
from ..avaspec import MeasConfigType, AVS_MeasureCallbackFunc
import numpy as np
import time

class Spectrometer:
    def __init__(self):
        self.avs = AvantesInterface()
        self.config = SpectrometerConfig.from_device(self.avs)
        self.data_ready = False
        self.spectral_data = np.zeros(self.config.pixels)

        # print(f"波長數據長度: {len(self.config.wavelength)}")
        # print(f"前 10 個波長: {self.config.wavelength[:10]}")

        # if np.any(self.config.calib_factors):
        #     print(f"強度校正數據 (前 10 筆): {self.config.calib_factors[:10,]}")
        # else:
        #     print("沒有強度校正數據!")

    def measure_once(self): # 回傳的光譜資料陣列
        print("準備進行單次測量...")
        self.data_ready = False


        measconfig = MeasConfigType()
        measconfig.m_StartPixel = 0
        measconfig.m_StopPixel = self.config.pixels - 1
        measconfig.m_IntegrationTime = 50.0
        measconfig.m_NrAverages = 1
        measconfig.m_Trigger_m_Mode = 0

        if self.avs.prepare_measure(measconfig) != 0:
            raise RuntimeError("AVS_PrepareMeasure 失敗")

        cb = AVS_MeasureCallbackFunc(self.handle_newdata)
        if self.avs.start_measurement(cb) != 0:
            raise RuntimeError("AVS_MeasureCallback 啟動失敗")

        return self.poll_for_scan()

    def poll_for_scan(self, timeout=5):
        print("正在等待光譜資料...")
        start_time = time.time()
        while not self.data_ready:
            if time.time() - start_time > timeout:
                raise RuntimeError("等待超時")
            if self.avs.poll_scan():
                print("掃描完成，等待回呼處理...")
            time.sleep(0.5)
        return self.spectral_data

    @pyqtSlot(int, int)
    def handle_newdata(self, lparam1, lparam2):
        print("接收新光譜資料中...")
        ret = self.avs.get_scope_data()
        if not ret or len(ret) < 2:
            raise RuntimeError("AVS_GetScopeData() 無效回傳")


        _, spectrum_data = ret
        self.spectral_data = np.array(spectrum_data)[:self.config.pixels]
        self.spectral_data = apply_calibration(self.spectral_data, self.config.calib_factors)

        self.data_ready = True

        print(f"光譜數據前 10 筆: {self.spectral_data[:10]}")
        if np.any(self.spectral_data < 0):
            print("警告：存在負值，可能需暗譜扣除")

    def get_spectral_data(self): # 每個像素對應的波長
        return self.spectral_data

    def get_wavelength(self):
        return self.config.wavelength
    
    def get_integration_time(self):
        return 50.0  # 單位毫秒，這是你在 measure_once() 中設定的值

    def close_spectrometer(self):
        self.avs.stop()
        self.avs.close()
        print("光譜儀已關閉")
