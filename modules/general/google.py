import glados
import urllib.parse


class Google(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('google', '<term>', 'Generate a google link')
        ]

    @glados.Module.commands('google')
    def google(self, message, term):
        if term == '':
            yield from self.provide_help('google', message)
            return
        q = urllib.parse.urlencode({'q': term})
        url = 'https://www.google.ch/search?{}'.format(q)
        yield from self.client.send_message(message.channel, url)

