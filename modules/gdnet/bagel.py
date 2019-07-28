import glados
import random


users_to_correct = {
    '235212704397262848'  # BagelBytes
}


class BagelCorrect(glados.Module):
    @glados.Module.rule('^.*(?i)(\\btho\\b|\\bdoe\\b).*$')
    async def tho(self, message, match):
        if message.author.id in users_to_correct:
            await self.client.send_message(message.channel, 'though*')
        return ()

    @glados.Module.rule('^.*(!i)\\bcuz\\b.*$')
    async def cuz(self, message, match):
        if message.author.id in users_to_correct:
            await self.client.send_message(message.channel, 'because*')
        return ()


class BagelHelp(glados.Module):
    @glados.Module.command('bagel', '', 'Post link to "how to ask a question"')
    @glados.Module.command('noob', '', 'Post link to "how to ask a question"')
    async def noob(self, message, content):
        await self.client.send_message(message.channel, "https://zellwk.com/blog/asking-questions/")


class BagelAMD64(glados.Module):
    @glados.Permissions.spamalot
    @glados.Module.rule('^.*$')
    async def amd64(self, message, match):
        if message.author.id in users_to_correct:
            if random.random() > 0.99:
                await self.client.send_message(message.channel, "amd64 😏")
        return ()

