from flask import Flask, render_template, Response
import time
import datetime
import random

# 你自己的函式庫：temp_py_package
from temp_py_package import continuous_read  

app = Flask(__name__)

# 以下為四組「歷史資料」及計數器（或其他變數），每個圖表對應一組
HISTORY_DATA_1 = []
HISTORY_DATA_2 = []
HISTORY_DATA_3 = []
HISTORY_DATA_4 = []

# ---------------------------------------------------------------------
# 首頁，指示用
@app.route('/')
def index():
    return '<a href="./chart_test">監控器</a>'

# ---------------------------------------------------------------------
# 主頁面：顯示所有圖表
@app.route('/chart_test')
def chart_test():
    """
    進入頁面時，將各圖表的歷史資料打包給前端作初始繪圖。
    """
    return render_template(
        "test.html", 
        history1=HISTORY_DATA_1,
        history2=HISTORY_DATA_2,
        history3=HISTORY_DATA_3,
        history4=HISTORY_DATA_4
    )

# ---------------------------------------------------------------------
# (1) SSE 路由：第一張圖 - 讀取 COM7 (continuous_read)
@app.route('/chart_value_1') #temp sensor
def chart_value_1():
    def generate_value_1():
        port = 'COM7'
        while True:
            # 讀取你的函式庫資料
            val = continuous_read(port)
            # 存入第一張圖的歷史資料
            HISTORY_DATA_1.append(val)

            # SSE 格式：以 "data:" 開頭，以 "\n\n" 結束
            yield f"data: {val}\n\n"

            time.sleep(0.5)  # 半秒推送一次，或自行調整
    return Response(generate_value_1(), mimetype="text/event-stream")

# ---------------------------------------------------------------------
# (2) SSE 路由：第二張圖 - 用計數器自增模擬
@app.route('/chart_value_2')
def chart_value_2():
    def generate_value_2():
        counter = 0
        while True:
            counter += 1
            HISTORY_DATA_2.append(counter)
            yield f"data: {counter}\n\n"
            time.sleep(0.5)  # 每秒推送一次
    return Response(generate_value_2(), mimetype="text/event-stream")

# ---------------------------------------------------------------------
# (3) SSE 路由：第三張圖 - 用隨機數模擬
@app.route('/chart_value_3')
def chart_value_3():
    def generate_value_3():
        while True:
            val = random.randint(0, 100)
            HISTORY_DATA_3.append(val)
            yield f"data: {val}\n\n"
            time.sleep(1)  # 每秒推送一次
    return Response(generate_value_3(), mimetype="text/event-stream")

# ---------------------------------------------------------------------
# (4) SSE 路由：第四張圖 - 用稍微不同的隨機或其他邏輯
@app.route('/chart_value_4')
def chart_value_4():
    def generate_value_4():
        while True:
            val = random.uniform(50, 150)  # 浮點數
            HISTORY_DATA_4.append(val)
            yield f"data: {val}\n\n"
            time.sleep(2)  # 每 2 秒推送一次
    return Response(generate_value_4(), mimetype="text/event-stream")


# ---------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
