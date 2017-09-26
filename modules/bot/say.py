import glados


class Say(glados.Module):

    def get_help_list(self):
        return [glados.Help('say', '<server> <channel> <message>', 'Have the bot send an arbitrary message to any server')]

    @glados.Permissions.owner
    @glados.Module.commands('say')
    async def say(self, message, content):
        parts = content.split(' ', 2)
        if len(parts) < 3:
            await self.provide_help('say', message)
            return

        # find relevant channel
        for channel in self.client.get_all_channels():
            if channel.server.id == parts[0] or channel.server.name == parts[0]:
                if channel.id == parts[1] or channel.name.strip('#') == parts[1].strip('#'):
                    await self.client.send_message(channel, parts[2])
                    return
        return tuple()
