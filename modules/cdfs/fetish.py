import glados


class Fetish(glados.Module):

    @glados.DummyPermissions.moderator
    @glados.DummyPermissions.command('fetish', '<user>', 'Grant the user access to the fetish channel')
    async def fetish(self, message, content):
        members, roles, error = self.parse_members_roles(message, content)
        if len(members) == 0:
            error = error if error else 'Couldn\'t find any users'
            await self.client.send_message(message.channel, error)
            return

        roles = [role for role in self.current_server.roles if role.name == 'Dirty Pony']
        for member in members:
            await self.client.add_roles(member, *roles)
        await self.client.send_message(message.channel,
            'Assigned "{}" to user(s) {}'.format(roles[0].name, ' '.join(x.name for x in members)))

    @glados.DummyPermissions.moderator
    @glados.DummyPermissions.command('unfetish', '<user>', 'Remove a user\'s access to the fetish channel')
    async def unfetish(self, message, content):
        members, roles, error = self.parse_members_roles(message, content)
        if len(members) == 0:
            error = error if error else 'Couldn\'t find any users'
            await self.client.send_message(message.channel, error)
            return

        roles = [role for role in self.current_server.roles if role.name == 'Dirty Pony']
        for member in members:
            await self.client.remove_roles(member, *roles)
        await self.client.send_message(message.channel,
            'Removed "{}" from user(s) {}'.format(roles[0].name, ' '.join(x.name for x in members)))
