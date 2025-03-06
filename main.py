from flask import Flask, render_template,Response
import time
from utils import Test
import datetime
app = Flask(__name__)

@app.route('/')
def index():
    # 取得現在時間（伺服器時間）
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 將時間傳遞給模板
    return render_template("test.html", time=current_time)

@app.route('/time_stream')
def time_stream():
    # 透過 SSE 不斷傳送當下時間
    def generate_time():
        while True:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            yield f"data: {now}\n\n"
            time.sleep(1)  # 每秒推送一次時間
    return Response(generate_time(), mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(debug=True)
