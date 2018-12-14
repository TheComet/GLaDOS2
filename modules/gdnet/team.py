from glados import Module


class Team(Module):
    @Module.command("team", "", "Get a link to the hobby classifieds forum")
    async def team(self, message, args):
        await self.client.send_message(message.channel, "Try the hobby classifieds forum: https://www.gamedev.net/forums/forum/29-hobby-project-classifieds/")

