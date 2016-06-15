import glados


class Test(glados.Module):

    @glados.Module.commands("test", "bar")
    def on_message(self, client, message, content):
        yield from client.send_message(message.channel, "hi!")
