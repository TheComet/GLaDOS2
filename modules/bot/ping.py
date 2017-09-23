import glados


class Ping(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('ping', '', 'pong')
        ]

    @glados.Module.commands('ping')
    async def ball(self, message, content):
        await self.client.send_message(message.channel, 'pong')
