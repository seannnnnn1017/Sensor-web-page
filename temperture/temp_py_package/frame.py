from .crc import calculate_crc

def build_request_frame(slave_addr, start_addr, num_words):
    """
    建構讀取指令封包 (Function code 03 - 讀取保持暫存器)
    :param slave_addr: 從站地址 (例如：0x03)
    :param start_addr: 起始位址 (例如：0x0000 表示 T1 Real-Time Data)
    :param num_words: 讀取字數 (1 word = 2 bytes)
    :return: 組成好的 bytearray 封包
    """
    frame = bytearray()
    frame.append(slave_addr)
    frame.append(0x03)  # 功能碼 03H
    frame.append((start_addr >> 8) & 0xFF)  # 起始位址高位
    frame.append(start_addr & 0xFF)         # 起始位址低位
    frame.append((num_words >> 8) & 0xFF)     # 字數高位
    frame.append(num_words & 0xFF)            # 字數低位
    crc = calculate_crc(frame)
    frame.append(crc & 0xFF)         # CRC 低位
    frame.append((crc >> 8) & 0xFF)  # CRC 高位
    return frame
