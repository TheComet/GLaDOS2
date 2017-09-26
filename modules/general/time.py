import glados
from time import gmtime, strftime


class Time(glados.Module):
    @glados.Module.command('time', '', 'Returns the time (completely useless)')
    async def time(self, message, arg):
        await self.client.send_message(message.channel, 'It is currently {}'.format(strftime('%H:%M:%S', gmtime())))
