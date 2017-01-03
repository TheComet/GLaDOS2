import glados
import random


responses = [
    'SHUT UP',
    'SHUT IT',
    'OH MY GOD',
    'オフファック'
]


class Saatchi(glados.Module):
    def get_help_list(self): return list()

    @glados.Module.bot_rules('^.*Boku.*$')
    def saatchi(self, message, match):
        if message.author.id == '247846577723408385':
            yield from self.client.send_message(message.channel, random.choice(responses))
