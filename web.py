import os
from flask import Flask, jsonify, Response

app = Flask(__name__)

@app.get('/')
def home():
    return Response('TrustMe AI Bot OK', mimetype='text/plain')

@app.get('/healthz')
def healthz():
    return jsonify(status='ok')

@app.get('/favicon.ico')
def fav():
    return ('', 204)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)))
