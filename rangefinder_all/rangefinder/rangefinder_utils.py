# # rangefinder_utils.py
# # 封裝感測器初始化與量測功能副程式模块

# import time
# from rangefinder import LKIF2Device
# from rangefinder.constants import RC_OK, LKIF_ABLEMODE_AUTO


# def initialize_sensor(device, out_no=0):
#     """
#     一次性初始化：包含 ABLE 校正與自動歸零
#     只要在整個批次啟動時呼叫一次即可
#     """
#     device.stop_measure()
#     # ABLE 校正
#     print(">>> 開始執行 ABLE 校正，請在 4–6 cm 範圍內緩慢移動標準板，按 Enter 結束校正")
#     device.dll.LKIF2_SetAbleMode(out_no, LKIF_ABLEMODE_AUTO)
#     device.dll.LKIF2_AbleStart(out_no)
#     input()
#     device.dll.LKIF2_AbleStop()
#     print(">>> ABLE 校正完成")

#     # 自動歸零
#     print(">>> 執行 Auto-zero")
#     device.stop_measure()
#     rc = device.dll.LKIF2_SetZeroSingle(out_no, 1)
#     print(f"Auto-zero 返迴碼：0x{rc:X}")
#     print(">>> Auto-zero 完成")


# def measure_once(device, out_no=0, sampling_us=1000, range_code=0, refl_mode=0):
#     """
#     單次量測：設定參數、啟動量測、讀一筆 VALID，回傳(relative, absolute)
#     absolute = basic_ref + relative
#     """
#     device.stop_measure()
#     device.dll.LKIF2_SetSamplingCycle(out_no, sampling_us)
#     device.dll.LKIF2_SetRange(out_no, range_code)
#     device.dll.LKIF2_SetReflectionMode(out_no, refl_mode)

#     device.start_measure()
#     while True:
#         d = device.read_single(out_no)
#         if d['FloatResult'] == 'VALID':
#             rel = d['Value']
#             # 假設 basic_ref 由呼叫者指定
#             return rel
#         time.sleep(0.005)


# def measure_continuous(device, num_samples=None, interval=0.1, basic_ref=50.0,
#                        sampling_us=1000, range_code=0, refl_mode=0, out_no=0):
#     """
#     持續量測：呼叫一次 initialize_sensor 後，連續取得(relative, absolute)資料
#     返回列表[(elapsed, abs, rel), ...]
#     """
#     results = []
#     start_t = time.time()

#     device.stop_measure()
#     device.dll.LKIF2_SetSamplingCycle(out_no, sampling_us)
#     device.dll.LKIF2_SetRange(out_no, range_code)
#     device.dll.LKIF2_SetReflectionMode(out_no, refl_mode)
#     device.dll.LKIF2_SetBasicPoint(out_no, 0)  # 參考點

#     device.start_measure()
#     count = 0
#     while True:
#         d = device.read_single(out_no)
#         if d['FloatResult'] == 'VALID':
#             rel = d['Value']
#             abs_dist = basic_ref + rel
#             elapsed = time.time() - start_t
#             results.append((elapsed, abs_dist, rel))
#             count += 1
#             if num_samples is not None and count >= num_samples:
#                 break
#             time.sleep(interval)
#         else:
#             time.sleep(0.005)
#     return results
