import glados
import json
import asyncio
import subprocess


class PushNotifier(glados.Module):
    def __init__(self):
        super(PushNotifier, self).__init__()
        self.__channels = None

    def setup(self):
        self.__channels = self.settings['git']['push notifier']['channels']
        asyncio.async(self.run())

    def get_help_list(self):
        return list()

    @asyncio.coroutine
    def run(self):
        ps = subprocess.Popen(('env/bin/python', 'listener.py'), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            loop = asyncio.get_event_loop()
            msg = yield from loop.run_in_executor(None, ps.communicate)
            msg = msg[0]
            try:
                data = json.loads(msg)
            except:
                continue

            author = data['commits'][0]['author']['name']
            message = data['commits'][0]['message']
            repo = data['repository']['name']
            msg = '"{}" pushed to {}: {}'.format(author, repo, message)
            for channel in self.client.get_all_channels():
                if channel.id in self.__channels:
                    yield from self.client.send_message(channel, msg)
