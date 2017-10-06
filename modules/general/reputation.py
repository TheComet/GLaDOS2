import glados
import codecs
import json
import os.path


class Reputation(glados.Module):

    def setup_memory(self):
        self.memory['reputation path'] = os.path.join(self.data_dir, 'reputation')
        if not os.path.exists(self.memory['reputation path']):
            os.makedirs(self.memory['reputation path'])
    
    def _update_reputation(self, data):
        rep_file = os.path.join(self.memory['reputation path'], 'reputation.json')
        with codecs.open(rep_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    
    def _get_reputation(self):
        rep_file = os.path.join(self.memory['reputation path'], 'reputation.json')
        if not os.path.exists(rep_file):
            return {}
        with codecs.open(rep_file, 'r', encoding='utf-8') as f:
            return json.load(f)

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
        reputation = self._get_reputation()
        for member in members:
            new_reputation = reputation.get(member.name, 0) + 1
            reputation[member.name] = new_reputation
            response.append('{}\'s reputation is {}'.format(member.name, new_reputation))
        self._update_reputation(reputation)
        await self.client.send_message(message.channel, ', '.join(response))

    @glados.Module.command('downvote', '<user>', 'Remove reputation from a user')
    async def downvote(self, message, content):
        members, roles, error = self.parse_members_roles(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return
        response = []
        reputation = self._get_reputation()
        for member in members:
            new_reputation = reputation.get(member.name, 0) - 1
            reputation[member.name] = new_reputation
            response.append('{}\'s reputation is {}'.format(member.name, new_reputation))
        self._update_reputation(reputation)
        await self.client.send_message(message.channel, ', '.join(response))

    @glados.Module.command('reputation', '<user>', 'See a user\'s reputation')
    async def reputation(self, message, content):
        members, roles, error = self.parse_members_roles(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return
        reputation = self._get_reputation()
        response = ['{}\'s reputation is {}'.format(member.name, reputation.get(member.name, 0)) for member in members ]
        await self.client.send_message(message.channel, ', '.join(response))
