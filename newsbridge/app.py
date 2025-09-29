from flask import Flask, render_template, jsonify, send_from_directory
from news_fetcher import get_all_china_news, FEEDS

app = Flask(__name__)

@app.route('/')
def index():
    news = get_all_china_news()
    sources = [name for name, _ in FEEDS]
    return render_template('index.html', news=news, sources=sources)


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/api/news')
def api_news():
    return jsonify(get_all_china_news())

if __name__ == '__main__':
    app.run(debug=True)
