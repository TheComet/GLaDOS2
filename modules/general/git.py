import glados
import json
import asyncio
import subprocess
import traceback


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
        ps = subprocess.Popen(('/home/cometbot/discord/GLaDOS2/github_webhook.py',), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print('started server')
        while True:
            loop = asyncio.get_event_loop()
            msg = yield from loop.run_in_executor(None, ps.stdout.readline)
            msg = msg.decode('utf-8')
            fixed_json = msg.split('127.0.0.1')[0]
            #fixed_json = broken_json.replace('"', '__tmp__').replace('"', "'").replace('__tmp__', "'").replace(': ,', ': "",').replace('True', '"True"').replace('False', '"False"').replace('None', '"None"')
            print('got message {}'.format(fixed_json))
            try:
                data = json.loads(fixed_json)
            except:
                tb = traceback.format_exc()
                print(tb)
                continue

            try:
                author = data['commits'][0]['author']['username']
                message = data['commits'][0]['message']
            except KeyError:
                author = data['commits'][0]['author']['name'] + ' the Rulebreaker'
                message = data['commits'][0]['message'] + ', but I fucked it up'
            repo = data['repository']['name']
            #added = data['commits'][0]['added']
            #removed = data['commits'][0]['removed']
            msg = '{} pushed to {}: "{}".'.format(author, repo, message)
            for channel in self.client.get_all_channels():
                if channel.id in self.__channels:
                    yield from self.client.send_message(channel, msg)

