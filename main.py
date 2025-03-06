from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    # 首頁介面
    return 'test'

@app.route('/page2')
def page2():
    # 第二個介面
    return 'test1'

if __name__ == '__main__':
    app.run(debug=True)
