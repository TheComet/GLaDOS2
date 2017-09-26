import glados


class Doot(glados.Module):
    @glados.Module.command(':dootdoot:', '', 'doot')
    async def ball(self, message, content):
        await self.client.send_message(message.channel, 'http://i2.kym-cdn.com/photos/images/newsfeed/000/376/360/77a.png')

