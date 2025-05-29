# spectrometer/calibration.py
# 負責處理光譜資料的強度校正邏輯，例如套用校正係數
import numpy as np

def apply_calibration(spectrum_data, calib_factors):
    """套用強度校正"""
    if np.any(calib_factors):
        return spectrum_data * calib_factors
    return spectrum_data
