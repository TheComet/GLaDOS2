import glados
import os

class Ayoub(glados.Module):
    @glados.Module.command('ayoub', '', 'For when you\'re feeling too rich')
    async def ayoub(self, message, args):
        await self.client.send_file(message.channel, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ayoub.jpg'))

