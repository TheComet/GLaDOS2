import glados


class DamnStraight(glados.Module):
    @glados.Module.rule("^.*(?=.*damn)(?=.*straight).*$")
    async def damn_straight(self, message, content):
        await self.client.send_message(message.channel, '{} Straighter than the pole your mom dances on?'.format(message.author.mention))
