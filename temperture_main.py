import threading
import sys
from temp_py_package import continuous_read

def shutdown():
    print("五分鐘已到，自動關閉程式。")
    sys.exit(0)

def main():
    port = 'COM3'
    timer = threading.Timer(-1, shutdown)
    timer.start()
    continuous_read(port)
    timer.cancel()

if __name__ == '__main__':
    main()
