import glados
import os


class Watchout(glados.Module):
    @glados.Module.command('watchout', '', 'Post the watchout picture Alpheus likes so much')
    async def watchout(self, message, args):
        await self.client.send_file(message.channel, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'watchout.jpg'))
