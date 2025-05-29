# globals.py
from dataclasses import dataclass, field
import numpy as np

@dataclass
class SpectrometerGlobals:
    # 光譜儀的裝置控制代碼（由 AVS_Activate() 回傳，0 表示尚未連接）
    dev_handle: int = 0

    # 像素數量（預設 2048，可根據實際裝置更新）
    pixels: int = 2048

    # 每個像素對應的波長資料（nm）
    wavelength: np.ndarray = field(default_factory=lambda: np.zeros(2048))

    # 每個像素對應的強度資料（光譜數據）
    spectraldata: np.ndarray = field(default_factory=lambda: np.zeros(2048))

    # 掃描次數紀錄（可用於統計）
    NrScanned: int = 0


# 實體化為單例，用來在整個程式中共用
globals = SpectrometerGlobals()

