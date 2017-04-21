import glados
import json
import asyncio
from flask import Flask, request

app = Flask(__name__)


class PushNotifier(glados.Module):
    def __init__(self):
        super(PushNotifier, self).__init__()
        self.__channels = None

    def setup(self):
        self.__channels = self.settings['git']['push notifier']['channels']
        asyncio.ensure_future(self.run())

    def get_help_list(self):
        return list()

    @asyncio.coroutine
    def run(self):
        app.run(port=8010)

    @app.route('/',methods=['POST'])
    def listener(self):
        data = json.loads(request.data)
        author = data['commits'][0]['author']['name']
        message = data['commits'][0]['message']
        repo = data['repository']['name']
        msg = '"{}" pushed to {}: {}'.format(author, repo, message)
        for channel in self.client.get_all_channels():
            if channel.id in self.__channels:
                yield from self.client.send_message(channel, msg)
        return list()
