import glados


class Reputation(glados.Module):
    reputation = {}

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
            response.append('{} reputation is {}'.format(member, new_reputation))
        await self.client.send_message(', '.join(response))
        return
