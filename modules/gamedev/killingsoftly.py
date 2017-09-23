import glados

class KillingSoftly(glados.Module):
    def get_help_list(self): return list()
    @glados.Module.rules('^({}|{}) ?(?!{}.*)$'.format(chr(0x1F52A), chr(0x1F5E1), chr(0x2601)))
    def post_cloud(self, message, match):
        await self.client.send_message(message.channel, chr(0x2601))
