import glados


class DamnStraight(glados.Module):
    @glados.Module.rule("^.*(?=.*damn)(?=.*straight).*$")
    async def damn_straight(self, message, content):
        await self.client.send_message('{} Straighter than the pole your mom dances on?', message.author.mention)
