import glados
import random


responses = [
    'SHUT UP',
    'SHUT IT',
    'OH MY GOD',
    'オフファック'
]


class Saatchi(glados.Module):
    @glados.Module.bot_rule('^.*Boku.*$')
    async def saatchi(self, message, match):
        if message.author.id == '247846577723408385':
            await self.client.send_message(message.channel, random.choice(responses))
