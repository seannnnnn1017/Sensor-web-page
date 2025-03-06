from temp_py_package import read_temperature, continuous_read

def main():
    port = 'COM3'
    continuous_read(port)

if __name__ == '__main__':
    main()
