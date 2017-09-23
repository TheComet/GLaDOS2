import glados
from time import gmtime, strftime


class Time(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('time', '', 'Returns the time (completely useless)')
        ]

    @glados.Module.commands('time')
    def time(self, message, arg):
        await self.client.send_message(message.channel, 'It is currently {}'.format(strftime('%H:%M:%S', gmtime())))
