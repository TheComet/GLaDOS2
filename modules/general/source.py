import glados

class Source(glados.Module):
    def get_help_list(self):
        return [glados.Help('source', '', 'Returns a link to the source code of GLaDOS')]
    
    @glados.Module.commands('source')
    def source(self, message, args):
        await self.client.send_message(message.channel, 'https://github.com/TheComet/GLaDOS2')

