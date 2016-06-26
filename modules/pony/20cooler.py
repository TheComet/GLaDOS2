import glados


class TwentyPercentCooler(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('20', '', 'Be twenty percent cooler')
        ]

    @glados.Module.commands('20')
    def on_twenty_percent_cooler(self, message, arg):
        if arg == '':
            target = message.author.name
        else:
            target = arg
        yield from self.client.send_message(message.channel, target + ' is now 20% cooler')
