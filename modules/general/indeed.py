import glados
import os


class Indeed(glados.Module):
    @glados.Module.command('indeed', '', 'Post the indeed picture Alpheus likes so much')
    async def indeed(self, message, args):
        await self.client.send_file(message.channel, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'indeed.jpg'))
