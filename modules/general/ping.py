import glados


class Ping(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('ping', '', 'pong')
        ]

    @glados.Module.commands('ping')
    def ball(self, message, content):
        yield from self.client.send_message(message.channel, 'pong')
