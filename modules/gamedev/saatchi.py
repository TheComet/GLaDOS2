import glados


class Saatchi(glados.Module):
    def get_help_list(self): return list()

    @glados.Module.rules('^Boku Saatchi\!$')
    def saatchi(self, message, match):
        yield from self.client.send_message(message.channel, 'SHUT UP')
