import glados


class Source(glados.Module):
    @glados.Module.command('source', '', 'Returns a link to the source code of GLaDOS')
    async def source(self, message, args):
        await self.client.send_message(message.channel, 'https://github.com/TheComet/GLaDOS2')
