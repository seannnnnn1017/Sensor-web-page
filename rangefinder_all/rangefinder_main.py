# rangefinder_main.py

import csv
import time
from rangefinder import LKIF2Device
from rangefinder.constants import RC_OK, LKIF_ABLEMODE_AUTO

# 參考距離 (mm)
BASIC_REF = 50.0  
# OUT 編號與參數設定
OUT_NO      = 0
SAMPLING_US = 1000  # µs
RANGE_CODE  = 0     # 0:4cm,1:10cm,2:20cm,3:40cm
refl_mode = 0  # 0:漫反射, 1:鏡面反射
interval = 0.1  # 測量間隔 (秒)

def initialize_sensor(device):
    """
    一次性初始化：ABLE 校正 + Auto-zero
    """
    device.stop_measure()
    print(">>> ABLE 校正: 請在 4–6 cm 範圍內移動標準板，按 Enter 繼續...")
    device.dll.LKIF2_SetAbleMode(OUT_NO, LKIF_ABLEMODE_AUTO)
    device.dll.LKIF2_AbleStart(OUT_NO)
    input()
    device.dll.LKIF2_AbleStop()
    print(">>> Auto-zero")
    device.stop_measure()
    device.dll.LKIF2_SetZeroSingle(OUT_NO, 1)
    print(">>> 初始化完成\n")


def single_measure_csv(filename='single_measure.csv', refl_mode=refl_mode):
    """
    單次測量：讀取一筆有效值並存成 CSV
    格式：elapsed(s), absolute(mm), relative(mm)
    """
    device = LKIF2Device()
    start_t = time.time()
    try:
        rc = device.open()
        if rc != RC_OK:
            raise RuntimeError(f"Open 失敗: 0x{rc:X}")
        initialize_sensor(device)

        # 參數設定
        device.stop_measure()
        device.dll.LKIF2_SetSamplingCycle(OUT_NO, SAMPLING_US)
        device.dll.LKIF2_SetRange(OUT_NO, RANGE_CODE)
        device.dll.LKIF2_SetReflectionMode(OUT_NO, refl_mode)
        device.dll.LKIF2_SetBasicPoint(OUT_NO, 0)

        # 量測
        device.start_measure()
        while True:
            d = device.read_single(OUT_NO)
            if d['FloatResult'] == 'VALID':
                rel = d['Value']
                abs_dist = BASIC_REF + rel
                elapsed = time.time() - start_t
                # 寫檔
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Elapsed(s)', 'Absolute(mm)', 'Relative(mm)'])
                    writer.writerow([f"{elapsed:.3f}", f"{abs_dist:.3f}", f"{rel:.3f}"])
                print(f"結果已寫入 {filename}")
                break
            time.sleep(0.005)
    finally:
        device.close()


def continuous_measure_csv(filename='continuous_measure.csv', interval=interval, refl_mode=refl_mode):
    """
    持續測量（無限迴圈）：直到按 Ctrl+C 停止
    即時顯示並將時間/絕對距離/相對距離 寫入 CSV
    :param filename: 輸出 CSV 檔案名稱
    :param interval: 讀值間隔（秒）
    :param refl_mode: 反射模式 (0: 漫反射, 1: 鏡面反射)
    """
    device = LKIF2Device()
    start_t = time.time()
    try:
        rc = device.open()
        if rc != RC_OK:
            raise RuntimeError(f"Open 失敗: 0x{rc:X}")
        initialize_sensor(device)

        # 參數設定
        device.stop_measure()
        device.dll.LKIF2_SetSamplingCycle(OUT_NO, SAMPLING_US)
        device.dll.LKIF2_SetRange(OUT_NO, RANGE_CODE)
        device.dll.LKIF2_SetReflectionMode(OUT_NO, refl_mode)
        device.dll.LKIF2_SetBasicPoint(OUT_NO, 0)
        device.start_measure()

        # 開啟 CSV 並寫 header
        f = open(filename, 'w', newline='')
        writer = csv.writer(f)
        writer.writerow(['Elapsed(s)', 'Absolute(mm)', 'Relative(mm)'])
        f.flush()

        print('開始連續測量，按 Ctrl+C 結束並保存...')
        while True:
            d = device.read_single(OUT_NO)
            if d['FloatResult'] == 'VALID':
                rel = d['Value']
                abs_dist = BASIC_REF + rel
                elapsed = time.time() - start_t
                # 顯示於終端
                print(f"{elapsed:.3f}s | Abs: {abs_dist:.3f} mm | Rel: {rel:.3f} mm")
                # 寫入 CSV
                writer.writerow([f"{elapsed:.3f}", f"{abs_dist:.3f}", f"{rel:.3f}"])
                f.flush()
                time.sleep(interval)
            else:
                time.sleep(0.005)
    except KeyboardInterrupt:
        print('測量中斷，保存文件並關閉裝置。')
    finally:
        try: f.close()
        except: pass
        device.close()


if __name__ == '__main__':
    # 單次測量，執行後立刻結束
    # single_measure_csv()
         
    # 連續測量，按 Ctrl+C 結束
    continuous_measure_csv()