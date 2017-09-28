import glados


class AutoBump(glados.Module):
    @glados.Module.bot_rule('^.*Don\'t forget to bump the server.*$')
    async def do_bump(self, message, content):
        await self.client.send_message(message.channel, '=bump')
