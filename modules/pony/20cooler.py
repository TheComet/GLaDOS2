import glados


class TwentyPercentCooler(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('20', '', 'Be twenty percent cooler')
        ]

    @glados.Module.commands('20')
    def on_twenty_percent_cooler(self, client, message, arg):
        yield from client.send_message(message.channel, message.author.name + ' is now 20% cooler')
