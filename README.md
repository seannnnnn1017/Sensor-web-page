# Sensor-web-page

## 專案簡介
Sensor-web-page 是一套多感測器資料整合與即時監控平台，支援溫度感測器（RS485/Modbus）、音訊監測（麥克風）、AvaSpec 光譜儀、KEYENCE LK-G5000 雷射測距儀等多種裝置。提供 Tkinter 圖形化操作介面與 Flask SSE 網頁即時監控，適用於實驗室、工業現場等多感測應用。

---

## 主要功能
- **溫度感測**：即時讀取 RS485/Modbus 溫度感測器數據。
- **音訊監測**：支援錄音、即時波形/頻譜/聲音熱圖顯示，並可儲存 TDMS/CSV。
- **光譜儀資料收集**：AvaSpec 光譜儀即時量測、繪圖與自動儲存。
- **雷射測距儀**：KEYENCE LK-G5000 單次/連續量測、資料儲存與顯示。
- **圖形化操作介面**：Tkinter 整合多感測器監控、參數設定、即時圖表。
- **網頁即時監控**：Flask SSE 多圖表即時資料推送，支援多用戶瀏覽。

---

## 目錄結構
```
Sensor-web-page/
├── main_csv.py                # Tkinter 多感測器整合主程式
├── main_csv_test.py           # 測試用 GUI 主程式
├── main_web.py                # Flask SSE 網頁即時監控主程式
├── temperture_main.py         # 單純溫度感測器讀取腳本
├── sound_main.py              # 單純音訊監測腳本
├── spectrum_main.py           # 單純光譜儀資料收集腳本
├── rangefinder_main.py        # 單純雷射測距儀腳本
├── rangefinder/               # 測距儀驅動與工具
├── temp_py_package/           # 溫度感測器通訊協定與驅動
├── signal_package/            # 音訊錄音、處理、儲存模組
├── spectrum_py_package/       # 光譜儀通訊與資料處理
├── utils/                     # 工具函式
├── templates/                 # Flask 前端 HTML 模板
├── spectra_logs/              # 光譜資料儲存資料夾
├── environment.yml            # Conda 環境設定檔
├── .gitignore
└── README.md
```

---

## 建議使用 Conda 環境

本專案建議使用 Conda 來管理 Python 執行環境，已提供 `environment.yml` 供快速建立一致的開發環境。

### 建立與啟用環境

1. 安裝 [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 或 [Anaconda](https://www.anaconda.com/products/distribution)。
2. 於終端機進入專案資料夾，執行以下指令建立環境：
   ```sh
   conda env create -f environment.yml
   ```
3. 啟用環境：
   ```sh
   conda activate sensor
   ```
4. 建議於 VS Code 選擇此 Conda 環境作為 Python 解譯器，以確保相依套件正確。

---

## 執行方式

### 1. 圖形化多感測器整合（推薦）
```sh
python main_csv.py
```
- 啟動 Tkinter 視窗，整合溫度、音訊、測距儀即時監控與圖表。

### 2. 單一感測器測試
- 溫度感測器：
  ```sh
  python temperture_main.py
  ```
- 音訊監測：
  ```sh
  python sound_main.py
  ```
- 光譜儀：
  ```sh
  python spectrum_main.py
  ```
- 測距儀：
  ```sh
  python rangefinder_main.py
  ```

### 3. 網頁即時監控
```sh
python main_web.py
```
- 啟動 Flask 伺服器，瀏覽器開啟 [http://localhost:5000/chart_test](http://localhost:5000/chart_test) 查看即時圖表。

---

## 子系統與模組說明

### temp_py_package
- 溫度感測器通訊協定、CRC、封包解析、連線與資料讀取（支援 Modbus RTU）。

### signal_package
- 音訊錄音（`audio_recorder.py`）、訊號處理（`signal_processor.py`）、頻譜/熱圖儲存（`audio_save.py`）、單機測試（`sound_main.py`）。

### spectrum_py_package
- 光譜儀驅動、校正、資料解析、即時繪圖與儲存。

### rangefinder
- KEYENCE LK-G5000 測距儀 DLL 介接、參數設定、資料讀取、錯誤處理。

### utils
- 各類輔助函式與測試腳本。

### templates
- Flask 前端 HTML 模板（如 `test.html`）。

---

## 常見問題

- **Q: 執行時找不到 DLL/Lib？**
  - 請確認驅動檔案（如 `LKIF2.dll`、`avaspecx64.dll`）已放置於專案根目錄或系統路徑下。
- **Q: 音訊裝置無法偵測？**
  - 請確認麥克風已正確連接，並安裝對應驅動。
- **Q: Flask 頁面無法顯示即時資料？**
  - 請確認感測器已連接，且後端程式無錯誤。

---

## 版權與授權
本專案採用 MIT License，歡迎自由使用、修改與發佈。

---

## 聯絡方式
如有問題或建議，請於 GitHub 提出 issue 或聯絡專案