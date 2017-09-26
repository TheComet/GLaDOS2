import glados
import urllib.parse


class Google(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('google', '<term>', 'Generate a google link')
        ]

    @glados.Module.commands('google')
    async def google(self, message, term):
        if term == '':
            await self.provide_help('google', message)
            return
        q = urllib.parse.urlencode({'q': term})
        url = 'https://www.google.com/search?{}'.format(q)
        await self.client.send_message(message.channel, url)

