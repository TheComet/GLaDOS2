import glados


reputation = {}

class Reputation(glados.Module):

    @glados.Module.command('upvote', '<user>', 'Add reputation to a user')
    async def upvote(self, message, content):
        members, roles, error = self.parse_members_roles(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return
        if message.author in members:
            await self.client.send_message(message.channel, '{}, you should not upvote yourself.'.format(message.author.name))
            return
        response = []
        for member in members:
            new_reputation = reputation.get(member, 0) + 1
            reputation[member] = new_reputation
            response.append('{}\'s reputation is {}'.format(member.name, new_reputation))
        await self.client.send_message(message.channel, ', '.join(response))

    @glados.Module.command('downvote', '<user>', 'Remove reputation from a user')
    async def downvote(self, message, content):
        members, roles, error = self.parse_members_roles(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return
        response = []
        for member in members:
            new_reputation = reputation.get(member, 0) - 1
            reputation[member] = new_reputation
            response.append('{}\'s reputation is {}'.format(member.name, new_reputation))
        await self.client.send_message(message.channel, ', '.join(response))

    @glados.Module.command('reputation', '<user>', 'See a user\'s reputation')
    async def reputation(self, message, content):
        members, roles, error = self.parse_members_roles(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return
        response = ['{}\'s reputation is {}'.format(member.name, reputation.get(member, 0)) for member in members ]
        await self.client.send_message(message.channel, ', '.join(response))
