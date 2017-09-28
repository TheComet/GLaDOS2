import glados


users_to_correct = [
    '235212704397262848'  # BagelBytes
]


class BagelCorrect(glados.Module):
    @glados.Module.rule('^.*(?i)\\btho\\b.*$')
    async def tho(self, message, match):
        if message.id in users_to_correct:
            await self.client.send_message(message.channel, 'though*')
        return ()

    @glados.Module.rule('^.*(!i)\\bcuz\\b.*$')
    async def cuz(self, message, match):
        if message.id in users_to_correct:
            await self.client.send_message(message.channel, 'because*')
        return ()
