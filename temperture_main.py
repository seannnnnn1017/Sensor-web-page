from temp_py_package import continuous_read
import time

def main():
    port = 'COM7'
    while True:
        temp = continuous_read(port)
        if temp is not None:
            print("{:.1f}度C".format(temp))
        else:
            print("讀取溫度失敗")
        time.sleep(1)

if __name__ == '__main__':
    main()