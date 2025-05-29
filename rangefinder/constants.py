# constants.py
# 定義常數、錯誤碼以及測量結果狀態字串
# 這些常數用於驗證 DLL 呼叫結果與顯示對應的狀態資訊

# 回傳碼 (Return Codes)
RC_OK = 0x0000

RC_CODES = {
    0x0000: "Success",
    0x1001: "Command Error",
    0x1002: "Command Length Error",
    0x2000: "Open Device Failed",
    0x2001: "Device Not Opened",
    # ...根據需要可以擴充其他錯誤碼
}

# 測量結果狀態 (Float Result Status)
FLOAT_RESULT = {
    0: "VALID",            # 正常數據
    1: "+RANGEOVER",       # 超過正向量測範圍
    2: "-RANGEOVER",       # 超過負向量測範圍
    3: "WAITING",          # 等待中（資料尚未更新）
    4: "ALARM",            # 警告狀態（異常數值）
    5: "INVALID"           # 無效數據
}

# ABLE 模式 (自動/手動)
LKIF_ABLEMODE_AUTO = 0    # Automatic mode
LKIF_ABLEMODE_MANUAL = 1  # Manual mode
