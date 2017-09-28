import glados


class Say(glados.Module):
    @glados.Permissions.owner
    @glados.Module.command('say',  '<server> <channel> <message>', 'Have the bot send an arbitrary message to any server')
    async def say(self, message, content):
        try:
            channel, msg = self.get_channel_and_msg(message, content)
        except:
            return ()
        await self.client.send_message(channel, msg)

    def get_channel_and_msg(self, message, content):
        parts = content.split(' ')
        server, i = self.get_server(parts)
        channel, i = self.get_channel(i, parts, server)
        msg = self.get_message(i, parts)
        return channel, msg

    def get_server(self, parts):
        for server in self.client.servers:
            if server.id == parts[0]:
                return server, 1
            for i in range(len(parts)):
                if server.name == ' '.join(parts[0:i + 1]):
                    return server, i+1
        return None, None

    @staticmethod
    def get_channel(i, parts, server):
        for channel in server.channels:
            if channel.id == parts[i]:
                return channel, i+1
            for n in range(i, len(parts)):
                if channel.name == ' '.join(parts[i:n+1]):
                    return channel, n+1

    @staticmethod
    def get_message(i, parts):
        return parts[i:]
