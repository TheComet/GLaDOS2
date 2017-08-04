import glados

class ShouldOf(glados.Module):
    def get_help_list(self):
        return list()
    @glados.Module.rules('^.*(?i)(sh|c|w)ould of.*$')
    def shouldof(self, message, match):
        yield from self.client.send_message(message.channel, '{}ould have*'.format(match.group(1)))
