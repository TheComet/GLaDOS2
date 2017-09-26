import glados


class Ping(glados.Module):
    @glados.Module.command('ping', '', 'pong')
    async def ball(self, message, content):
        await self.client.send_message(message.channel, 'pong')
