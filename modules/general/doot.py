import glados


class Doot(glados.Module):

    def get_help_list(self):
        return [
            glados.Help(':dootdoot:', '', 'doot')
        ]

    @glados.Module.commands(':dootdoot:')
    def ball(self, message, content):
        await self.client.send_message(message.channel, 'http://i2.kym-cdn.com/photos/images/newsfeed/000/376/360/77a.png')

