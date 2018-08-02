import glados


class Fetish(glados.Module):

    @glados.Permissions.command('fetish', '', 'Grant yourself access to the fetish channels')
    async def fetish(self, message, content):
        roles = [role for role in self.server.roles if role.name == 'Dirty Pony']
        await self.client.add_roles(message.author, *roles)
        await self.client.send_message(message.channel,
            'Assigned "{}" to user {}'.format(roles[0].name, message.author.name))

    @glados.Permissions.command('unfetish', '', 'Remove your access to the fetish channels')
    async def unfetish(self, message, content):
        roles = [role for role in self.server.roles if role.name == 'Dirty Pony']
        await self.client.remove_roles(message.author, *roles)
        await self.client.send_message(message.channel,
            'Removed "{}" from user {}'.format(roles[0].name, message.author.name))
