import glados


class Test(glados.Module):

    def get_help_list(self):
        return list()

    @glados.Module.commands('test')
    def test(self, message, arg):
        yield from client.send_message(message.channel, 'test')
