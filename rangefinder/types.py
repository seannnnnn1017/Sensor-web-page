# types.py
# 這裡我們定義了 LKIF_FLOATVALUE_OUT 結構體，用於接收單一測量值

from ctypes import Structure, c_int, c_float

class LKIF_FLOATVALUE_OUT(Structure):
    """
    此結構體用於接收由 LKIF2_GetCalcDataSingle 函式返回的測量數值資訊

    Fields:
        OutNo (int): 代表測量輸出的編號
        FloatResult (int): 結果狀態（例如，0 表示正常，其他數值表示異常）
        Value (float): 真實的測量數值
    """
    _fields_ = [
        ("OutNo", c_int),
        ("FloatResult", c_int),
        ("Value", c_float)
    ]
