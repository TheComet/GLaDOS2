import glados


class ShouldOf(glados.Module):
    def get_help_list(self):
        return list()

    @glados.Module.rules('^.*(?i)((sh|c|w)ould|might)\\s+of\\b.*$')
    async def shouldof(self, message, match):
        await self.client.send_message(message.channel, '{} have*'.format(match.group(1)))
