import glados


class Blog(glados.Module):
    @glados.Module.command('blog', '', 'Returns a link to the chat blog')
    async def blog(self, message, channel):
        await self.client.send_message(message.channel, 'http://gdnetchat.tumblr.com/submit')

