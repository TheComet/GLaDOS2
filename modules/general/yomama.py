from glados import Module
from os.path import join, dirname, realpath
from random import choice

DB_FILE = join(dirname(realpath(__file__)), 'yomama.db')


class YoMama(Module):
    @Module.command('yomama', '', 'Generate a random Yo Mama joke')
    async def yomama(self, message, content):
        with open(DB_FILE, 'r') as f:
            joke = choice(f.read().splitlines())
            await self.client.send_message(message.channel, joke)

