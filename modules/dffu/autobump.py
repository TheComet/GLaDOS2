import glados


class AutoBump(glados.Module):
    @glados.Module.bot_rule('^.*Don\'t forget to bump the server.*$')
    async def do_bump(self, message, content):
        for i in range(5):  # Are they really this retarded?
            await self.client.send_message(message.channel, '=bump')
