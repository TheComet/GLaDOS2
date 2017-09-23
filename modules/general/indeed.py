import glados
import os

class Indeed(glados.Module):
    def get_help_list(self):
        return [glados.Help('indeed', '', 'Post the indeed picture Alpheus likes so much')]
    @glados.Module.commands('indeed')
    def indeed(self, message, args):
        await self.client.send_file(message.channel, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'indeed.jpg'))

