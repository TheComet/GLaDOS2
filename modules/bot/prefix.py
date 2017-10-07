from glados import Module, DummyPermissions


class Prefix(Module):
    @DummyPermissions.admin
    @Module.command('prefix', '<prefix>', 'Sets the command prefix for the current server. Default is "."')
    async def set_prefix(self, message, content):
        content = content.strip()
        if len(content) > 3:
            await self.client.send_message(message.channel, 'Are you sure about that')
            return

        was = self.command_prefix
        new = self.settings['command prefix'][self.current_server.id] = content
        await self.client.send_message(message.channel, 'Changed command prefix from `{}` to `{}`'.format(was, new))
