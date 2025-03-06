from flask import Flask, render_template, Response
import time
import datetime
import random
app = Flask(__name__)

# 全域列表用於儲存歷史資料（僅作示範，實際建議存資料庫）
HISTORY_DATA = []
COUNTER = 0  # 簡單的計數器

@app.route('/')
def index():
    return '<h1>首頁：請前往 /chart_test 查看折線圖</h1>'

@app.route('/chart_test')
def chart_test():
    """
    進入折線圖頁面前，
    先將已累積的 HISTORY_DATA 傳給前端作初始繪圖。
    """
    return render_template("test.html", history=HISTORY_DATA)

@app.route('/chart_value')
def chart_value():
    """
    SSE 路由：每秒產生一個新數值，推給前端，並寫入 HISTORY_DATA 中。
    """
    def generate_value():
        global COUNTER, HISTORY_DATA
        while True:
            COUNTER =random.randint(1,100)
            # 將新值加入到全域的歷史資料清單裡
            HISTORY_DATA.append(COUNTER)

            # SSE格式：必須以 'data:' 開頭，並以 '\n\n' 結束一筆訊息
            yield f"data: {COUNTER}\n\n"

            time.sleep(0.1)  # 每秒送一次
    return Response(generate_value(), mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(debug=True)
