import glados

class Blog(glados.Module):
    def get_help_list(self):
        return [
            glados.Help('blog', '', 'Returns a link to the chat blog')
        ]

    @glados.Module.commands('blog')
    def blog(self, message, channel):
        await self.client.send_message(message.channel, 'http://gdnetchat.tumblr.com/submit')

