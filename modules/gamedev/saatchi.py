import glados


class Saatchi(glados.Module):
    def get_help_list(self): return list()

    @glados.Module.rules('^Boku Saatchi\!$')
    def saatchi(self, client, message, match):
        yield from client.send_message(message.channel, 'SHUT UP')

