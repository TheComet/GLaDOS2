import random
from glados import Module
import dice


class Dice(Module):
    @Module.command('roll', '[number of sides]', 'Rolls a die. Defaults to 6')
    async def roll(self, message, args):
        if not args:
            args = 'd6'
        try:
            if args.endswith('+'):
                msg = str(sum(x for x in dice.roll(args.strip('+'))))
            else:
                msg = ', '.join(str(x) for x in dice.roll(args))
            await self.client.send_message(message.channel, msg)
        except Exception as e:
            print(e)
            await self.client.send_message(message.channel, 'Rolled way too hard')

