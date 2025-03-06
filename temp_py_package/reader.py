import serial
import time
from .frame import build_request_frame
from .parser import parse_response, convert_raw_to_temperature

def read_temperature(ser, slave_addr=0x03, start_addr=0x0000, num_words=1):
    """
    發送讀取溫度的指令，並回傳轉換後的溫度值
    :param ser: 已開啟的 serial 連線
    :param slave_addr: 從站地址
    :param start_addr: 起始讀取位址
    :param num_words: 讀取字數 (預設讀取 1 word 即 T1 資料)
    :return: 轉換後的溫度值 (若失敗則傳回 None)
    """
    # 建構指令封包
    frame = build_request_frame(slave_addr, start_addr, num_words)
    ser.write(frame)
    # 根據範例，預計回應 7 個 byte (若讀取 1 word)
    response = ser.read(7)
    if len(response) < 7:
        return None
    raw_value = parse_response(response)
    if raw_value is None:
        return None
    return convert_raw_to_temperature(raw_value)

def continuous_read(port, baudrate=57600):
    """
    每呼叫一次連接 serial port、讀取一次溫度資料並回傳讀取結果
    :param port: Serial port
    :param baudrate: 傳輸速率 (預設 57600)
    :return: 溫度數值 (若失敗則回傳 None)
    """
    try:
        ser = serial.Serial(port, baudrate, bytesize=8, parity='N', stopbits=1, timeout=1)
    except Exception as e:
        print("無法開啟 serial port:", e)
        return None

    try:
        temp = read_temperature(ser)
        return temp
    finally:
        ser.close()