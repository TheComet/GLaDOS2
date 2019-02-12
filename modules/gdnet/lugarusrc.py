import random
from glados import Module
from os.path import join, dirname, realpath


class LugaruSrc(Module):
    @Module.command('lugaru', '', 'Gets a random line of source code from lugaru')
    async def lugarusrc(self, message, args):
        filename = join(dirname(realpath(__file__)), 'lugarusrc.cpp')
        lines = open(filename).readlines()
        while True:
            line = random.choice(lines)
            if len(line.strip()) > 80:
                break
        line = line.strip()
        line = line[:980]  # You never know
        await self.client.send_message(message.channel, '```cpp\n' + line + '```')

