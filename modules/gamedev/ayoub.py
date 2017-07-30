import glados
import os

class Ayoub(glados.Module):
    def get_help_list(self): return [glados.Help('ayoub', '', 'For when you\'re feeling too rich')]

    @glados.Module.commands('ayoub')
    def ayoub(self, message, args):
        yield from self.client.send_file(message.channel, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ayoub.jpg'))

