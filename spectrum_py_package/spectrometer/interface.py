# spectrometer/interface.py
# 封裝所有 Avantes DLL 操作函式，提供簡單乾淨的裝置控制介面
from ..avaspec import *

class AvantesInterface:
    def __init__(self):
        ret = AVS_Init(0)
        if ret <= 0:
            raise RuntimeError("沒有找到光譜儀!")

        self.devices = AVS_GetList(1)
        if len(self.devices) == 0:
            raise RuntimeError("無可用設備!")

        self.dev_handle = AVS_Activate(self.devices[0])
        print(f"啟動光譜儀: {self.devices[0].SerialNumber.decode('utf-8')}")

    def get_parameter(self):
        return AVS_GetParameter(self.dev_handle, 63484)

    def get_lambda(self):
        return AVS_GetLambda(self.dev_handle)

    def prepare_measure(self, measconfig):
        return AVS_PrepareMeasure(self.dev_handle, measconfig)

    def start_measurement(self, callback_func):
        return AVS_MeasureCallback(self.dev_handle, callback_func, 1)

    def poll_scan(self):
        return AVS_PollScan(self.dev_handle)

    def get_scope_data(self):
        return AVS_GetScopeData(self.dev_handle)

    def stop(self):
        AVS_StopMeasure(self.dev_handle)

    def close(self):
        AVS_Done()
