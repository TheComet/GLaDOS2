import glados


class ShouldOf(glados.Module):
    @glados.Module.rule('^.*(?i)((sh|c|w)ould|might)\\s+of\\b.*$')
    async def shouldof(self, message, match):
        await self.client.send_message(message.channel, '{} have*'.format(match.group(1)))
