import random
from glados import Module
import dice


class Dice(Module):
    @Module.command('roll', '[number of sides]', 'Rolls a die. Defaults to 6')
    async def roll(self, message, args):
        if not args:
            args = 'd6'
        try:
            await self.client.send_message(message.channel, ', '.join(str(x) for x in dice.roll(args)))
        except:
            await self.client.send_message(message.channel, 'Rolled way too hard')

