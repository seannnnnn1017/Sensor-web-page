# spectrometer/config.py
# 負責從光譜儀設備讀取設定（像素數、波長、校正因子），並封裝為結構物件
import numpy as np

class SpectrometerConfig:
    def __init__(self, dev_handle, pixels, wavelength, calib_factors):
        self.dev_handle = dev_handle
        self.pixels = pixels
        self.wavelength = wavelength
        self.calib_factors = calib_factors

    @staticmethod
    def from_device(avs):
        """從光譜儀讀取參數，建立設定物件"""
        device_config = avs.get_parameter()
        pixels = device_config.m_Detector_m_NrPixels
        wavelength = np.array(avs.get_lambda())[:pixels]
        calib_factors = device_config.m_Irradiance_m_IntensityCalib_m_aCalibConvers[:pixels]

        return SpectrometerConfig(
            dev_handle=avs.dev_handle,
            pixels=pixels,
            wavelength=wavelength,
            calib_factors=calib_factors
        )
