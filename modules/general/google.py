import glados
import urllib.parse


class Google(glados.Module):
    @glados.Module.command('google', '<term>', 'Generate a google link')
    async def google(self, message, term):
        if term == '':
            await self.provide_help('google', message)
            return
        q = urllib.parse.urlencode({'q': term})
        url = 'https://www.google.com/search?{}'.format(q)
        await self.client.send_message(message.channel, url)

