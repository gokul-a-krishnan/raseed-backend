import os

if os.name != "nt" and os.name != "posix":
    __import__('pysqlite3')
    import sys

    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from dotenv import load_dotenv
from flask import Flask
from flask import request
from waitress import serve
from controller.receipt import receipt_blueprint
from controller.intelligent import intelligent_blueprint

load_dotenv(override=True)

app = Flask(__name__)


app.register_blueprint(receipt_blueprint, url_prefix='/receipt')
app.register_blueprint(intelligent_blueprint, url_prefix='/intelligent')


@app.route('/')
def index():
    return "Flask app!"


if __name__ == '__main__':
    print("Server running with eventlet...")
    serve(app, host='0.0.0.0', port=8180)
