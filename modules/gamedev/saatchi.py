import glados


responses = [
    'SHUT UP',
    'SHUT IT',
    'オフファック'
]


class Saatchi(glados.Module):
    def get_help_list(self): return list()

    @glados.Module.rules('^Boku Saatchi.*$')
    def saatchi(self, message, match):
        if message.author.name == 'Saatchi':
            yield from self.client.send_message(message.channel, 'SHUT UP')
