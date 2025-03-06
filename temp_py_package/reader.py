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

def continuous_read(port, baudrate=57600, interval=1):
    """
    持續讀取溫度資料並印出
    :param port: Serial port
    :param baudrate: 傳輸速率 (預設 57600)
    :param interval: 每次讀取間隔秒數 (預設 1 秒)
    """
    try:
        ser = serial.Serial(port, baudrate, bytesize=8, parity='N', stopbits=1, timeout=1)
    except Exception as e:
        print("無法開啟 serial port:", e)
        return

    print("開始讀取溫度資料 ...")
    try:
        while True:
            temp = read_temperature(ser)
            if temp is not None:
                print("{:.1f}度C".format(temp))
            else:
                print("讀取溫度失敗")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("使用者中斷，結束程式")
    finally:
        ser.close()
