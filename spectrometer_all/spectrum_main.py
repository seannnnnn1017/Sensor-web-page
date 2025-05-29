import os
import sys
import time
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from spectrum_py_package.spectrometer import Spectrometer

BUFFER_PATH = "spectra_logs/spectra_buffer.npy"
CSV_DIR = "spectra_logs"
os.makedirs(CSV_DIR, exist_ok=True)

def main():
    print("初始化光譜儀...")
    spec = Spectrometer()
    start_time = time.time()

    wavelength = spec.get_wavelength()
    integration_time_ms = spec.get_integration_time()
    if wavelength is None or len(wavelength) == 0:
        print("❌ 無效的波長數據，請檢查光譜儀連線！")
        sys.exit(1)

    wavelength = np.array(wavelength)
    valid_indices = wavelength > 0
    wavelength = wavelength[valid_indices]

    print("📡 收集 1 筆光譜資料...")
    spectral_data = spec.measure_once()
    if spectral_data is None or len(spectral_data) == 0:
        print("⚠️ 數據無效，結束。")
        return

    spectral_data = np.array(spectral_data)[valid_indices]
    elapsed_time = round(time.time() - start_time, 3)  # 單位：秒

    # 儲存當筆 csv
    filename = datetime.now().strftime("spectrum_%Y%m%d_%H%M%S.csv")
    output_path = os.path.join(CSV_DIR, filename)

    header = "Wavelength (nm),Intensity,Elapsed Time (s),Integration Time (ms)"
    data = np.column_stack([wavelength, spectral_data,
                            [elapsed_time]*len(wavelength),
                            [integration_time_ms]*len(wavelength)])
    np.savetxt(output_path, data, delimiter=",", fmt="%s", header=header, comments='')
    print(f"✅ 已儲存光譜資料到：{output_path}")

    # 更新 buffer
    if os.path.exists(BUFFER_PATH):
        spectra_buffer = np.load(BUFFER_PATH)
        spectra_buffer = np.vstack([spectra_buffer, spectral_data])
    else:
        spectra_buffer = np.array([spectral_data])
    np.save(BUFFER_PATH, spectra_buffer)

    # 顯示折線圖 + 熱圖
    fig, (ax_line, ax_heat) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [1, 1]})

    ax_line.plot(wavelength, spectral_data, label="Spectral Data", color="blue")
    ax_line.set_xlabel("Wavelength (nm)")
    ax_line.set_ylabel("Intensity")
    ax_line.set_title("Real-Time Spectrum")
    ax_line.grid(True)
    ax_line.legend()

    heatmap = ax_heat.imshow(np.nan_to_num(spectra_buffer),
                             aspect='auto',
                             extent=[wavelength[0], wavelength[-1], 0, spectra_buffer.shape[0]],
                             cmap='viridis',
                             origin='lower')
    ax_heat.set_xlabel("Wavelength (nm)")
    ax_heat.set_ylabel("Time (frames)")
    ax_heat.set_title("Spectral Heatmap Over Time")
    vmin = np.percentile(spectra_buffer, 1)
    vmax = np.percentile(spectra_buffer, 99)
    heatmap.set_clim(vmin=vmin, vmax=vmax)
    fig.colorbar(heatmap, ax=ax_heat, label="Intensity")

    plt.tight_layout()
    plt.show()

    spec.close_spectrometer()

if __name__ == "__main__":
    main()