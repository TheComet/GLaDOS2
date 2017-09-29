import glados
import asyncio


class AutoBump(glados.Module):
    @glados.Module.bot_rule('^.*Don\'t forget to bump the server.*$')
    async def do_bump(self, message, content):
        await asyncio.sleep(1)
        await self.client.send_message(message.channel, '=bump')
