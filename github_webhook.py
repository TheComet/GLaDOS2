#!/home/cometbot/discord/GLaDOS2/env/bin/python

from flask import Flask, request
import json

app = Flask(__name__)

@app.route('/',methods=['POST'])
def foo():
    print(request.data.decode('utf-8'))
    print('\n')
    return "OK"

if __name__ == '__main__':
   app.run(port=8010)
