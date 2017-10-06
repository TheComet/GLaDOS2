import glados


reputation = {}

class Reputation(glados.Module):

    @glados.Module.command('upvote', '<user>', 'Add reputation to a user')
    async def upvote(self, message, content):
        members, roles, error = self.parse_members_roles(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return
        response = []
        for member in members:
            new_reputation = reputation.get(member, 0) + 1
            reputation[member] = new_reputation
            response.append('{}\'s reputation is {}'.format(member.split('#')[0], new_reputation))
        await self.client.send_message(message.channel, ', '.join(response))
        return
