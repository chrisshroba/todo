from flask import *

app = Flask(__name__)

@app.route('/')
def root():
    return ["hello world"]

@app.after_request
def after_request(response):
    print "hi"

app.run(port=9999, debug = True)