def calculate_crc(data):
    """
    根據 Modbus RTU CRC16 算法計算 CRC 值
    :param data: bytearray 資料
    :return: 16-bit 整數 (CRC 值)
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc
