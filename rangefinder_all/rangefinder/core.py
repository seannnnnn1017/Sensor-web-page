# core.py
# 封裝與 LKIF2.dll 的互動，使用 ctypes 呼叫 DLL 函式
# 此模組提供 LKIF2Device 類別，可用於開啟裝置、設定參數、讀取測量值、以及關閉裝置

import ctypes
import os
from ctypes import byref, c_int, POINTER
from .types import LKIF_FLOATVALUE_OUT
from .constants import RC_OK, RC_CODES, FLOAT_RESULT

class LKIF2Device:
    """
    LKIF2Device 類別封裝了 LKIF2.dll 提供的函式，
    可用於對 LK-G5000 測距儀進行開啟、參數設定、量測與關閉操作。
    """
    def __init__(self, dll_path=None):
        """
        初始化裝置，載入 DLL

        Args:
            dll_path (str): 若未指定，預設會從執行主程式的工作目錄中尋找 LKIF2.dll
        """
        if dll_path is None:
            dll_path = os.path.abspath("LKIF2.dll")
        if not os.path.exists(dll_path):
            raise FileNotFoundError(f"❌ 找不到 DLL：{dll_path}")

        # 使用 WinDLL（stdcall 呼叫約定）
        self.dll = ctypes.WinDLL(dll_path)
        self._bind_functions()

    def _bind_functions(self):
        """
        為需要的 DLL 函式設定呼叫參數與返回類型
        """
        # ——— 開啟／關閉 裝置 ———
        self.dll.LKIF2_OpenDeviceUsb.restype        = c_int
        self.dll.LKIF2_CloseDevice.restype         = c_int

        # ——— 模式切換 ———
        self.dll.LKIF2_StopMeasure.restype         = c_int  
        self.dll.LKIF2_StartMeasure.restype        = c_int

        # ——— 讀取測量值 ———
        self.dll.LKIF2_GetCalcDataSingle.argtypes  = [
            c_int,                        # OutNo
            POINTER(LKIF_FLOATVALUE_OUT)  # *CalcData
        ]
        self.dll.LKIF2_GetCalcDataSingle.restype   = c_int

        # ——— 參數設定 ———
        # 取樣週期 (µs)
        self.dll.LKIF2_SetSamplingCycle.argtypes   = [c_int, c_int]
        self.dll.LKIF2_SetSamplingCycle.restype    = c_int
        # 量程編號
        self.dll.LKIF2_SetRange.argtypes           = [c_int, c_int]
        self.dll.LKIF2_SetRange.restype            = c_int
        # 反射模式 (0: 漫反射, 1: 鏡面反射)
        self.dll.LKIF2_SetReflectionMode.argtypes  = [c_int, c_int]
        self.dll.LKIF2_SetReflectionMode.restype   = c_int

        # ——— 校正命令 ———
        # 設定基準點 (Basic Point)
        self.dll.LKIF2_SetBasicPoint.argtypes      = [c_int, c_int]
        self.dll.LKIF2_SetBasicPoint.restype       = c_int
        # 瞬時自動歸零 (Auto-zero single)
        self.dll.LKIF2_SetZeroSingle.argtypes      = [c_int, c_int]
        self.dll.LKIF2_SetZeroSingle.restype       = c_int

        # —— ABLE 補正 (Auto-correction) ——
        # 設定 ABLE 模式 (Automatic / Manual)
        self.dll.LKIF2_SetAbleMode.argtypes        = [c_int, c_int]      # (HeadNo, LKIF_ABLEMODE_AUTO/MANUAL)
        self.dll.LKIF2_SetAbleMode.restype         = c_int
        # 設定 ABLE 控制範圍 (Min, Max)
        self.dll.LKIF2_SetAbleMinMax.argtypes      = [c_int, c_int, c_int]  # (HeadNo, Min, Max)
        self.dll.LKIF2_SetAbleMinMax.restype       = c_int
        # 開始 ABLE 校正
        self.dll.LKIF2_AbleStart.argtypes          = [c_int]              # (HeadNo)
        self.dll.LKIF2_AbleStart.restype           = c_int
        # 結束 ABLE 校正
        self.dll.LKIF2_AbleStop.argtypes           = []                    # (none)
        self.dll.LKIF2_AbleStop.restype            = c_int
        # 取消 ABLE 校正
        self.dll.LKIF2_AbleCancel.argtypes         = []                    # (none)
        self.dll.LKIF2_AbleCancel.restype          = c_int


    def open(self):
        """
        開啟 USB 裝置。成功時返回 RC_OK，否則拋出 RuntimeError。
        """
        rc = self.dll.LKIF2_OpenDeviceUsb()
        if rc != RC_OK:
            raise RuntimeError(f"OpenDevice 失敗：RC=0x{rc:X} ({RC_CODES.get(rc)})")
        return rc

    def close(self):
        """
        關閉已開啟的裝置，返回 RC code。
        """
        return self.dll.LKIF2_CloseDevice()

    def stop_measure(self):
        """
        切換到通訊模式（停止自動量測），返回 RC code。
        """
        return self.dll.LKIF2_StopMeasure()

    def start_measure(self):
        """
        切換回量測模式（開始自動量測），返回 RC code。
        """
        return self.dll.LKIF2_StartMeasure()

    def read_single(self, out_no=0):
        """
        讀取單一輸出（OUT）的測量資料

        Args:
            out_no (int): 要讀取的 OUT 編號，預設為 0

        Returns:
            dict: 包含 OutNo、RawStatus、FloatResult、Value 的字典

        Raises:
            RuntimeError: 當讀取失敗時，拋出異常並附上錯誤碼資訊
        """
        result = LKIF_FLOATVALUE_OUT()
        rc = self.dll.LKIF2_GetCalcDataSingle(out_no, byref(result))
        if rc != RC_OK:
            raise RuntimeError(f"Read failed：RC=0x{rc:X} ({RC_CODES.get(rc)})")
        return {
            "OutNo":     result.OutNo,
            "RawStatus": result.FloatResult,
            "FloatResult": FLOAT_RESULT.get(result.FloatResult, "Unknown"),
            "Value":     result.Value
        }
