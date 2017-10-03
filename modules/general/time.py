import glados
from datetime import datetime, timezone


class Time(glados.Module):
    @glados.Module.command('time', '', 'Returns the time (completely useless)')
    async def time(self, message, arg):
        await self.client.send_message(message.channel, 'It is currently {}'.format(
            datetime.now(timezone.utc).isoformat()))
