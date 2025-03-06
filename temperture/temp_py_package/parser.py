def parse_response(response):
    """
    解析回應封包，假設回應格式為：
    [Slave address, Function, Byte count, Data Hi, Data Lo, CRC Lo, CRC Hi]
    :param response: 接收到的 bytearray
    :return: raw 數值 (兩個位元組組成的整數)
    """
    if len(response) < 7:
        return None

    data_hi = response[3]
    data_lo = response[4]
    raw_value = (data_hi << 8) | data_lo
    return raw_value

def convert_raw_to_temperature(raw_value):
    """
    根據說明書中轉換公式 (raw_value - 4000) / 10 得到實際溫度
    :param raw_value: 讀取到的原始數值
    :return: 溫度 (攝氏度)
    """
    return (raw_value - 4000) / 10.0
