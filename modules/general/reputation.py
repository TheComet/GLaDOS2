import glados
import codecs
import json
import os.path
import random


COMEBACKS = [
    '{}, whom are you trying to fool?',
    '{}, you should not upvote yourself.',
    'Listen everypony, {} is trying to upvote himself!',
    'Listen everypony, {} is trying to upvote herself!',
    'I think you are a bit full of yourself, {}.',
    'One day you might get downvoted instead, {}.',
    'Thou shalt not upvote thyself.',
    'You think you\'re slick, huh?',
    'Trying to get a head start, aren\'t we, {}?',
    'I suggest you change your username to *Narcissus* instead, {}.',
    'That\'s not what they mean by "one person, one vote".',
    'Psssh. Not today, sweetie. Not today.',
    'Try not to flatter yourself too much, okay?',
    'YOLO, vote all the {}s!',
    'Did you just assume your vote, {}?',
    'Doesn\'t anybody else like you, {}',
    'Did you really think that would work, {}?',
    '{} is upvoting himself because nopony else would.',
    '{} is upvoting herself because nopony else would.',
    'Nope.',
    'A big fat no.',
]

DEFAULT_CONFIG = {
    daily_limit: 200,
}

class Reputation(glados.Module):

    def setup_memory(self):
        rep_file = os.path.join(self.data_dir, 'reputation', 'reputation.json')
        comebacks_file = os.path.join(self.data_dir, 'reputation', 'comebacks.json'),
        config_file = os.path.join(self.data_dir, 'reputation', 'config.json')
        self.memory['reputation'] = {
            'reputation': rep_file,
            'comebacks': comebacks_file,
            'config': config_file,
        }
        if not os.path.exists(rep_file):
            with codecs.open(rep_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
        if not os.path.exists(comebacks_file):
            with codecs.open(comebacks_file, 'w', encoding='utf-8') as f:
                json.dump(COMEBACKS, f)
        if not os.path.exists(config_file):
            with codecs.open(config_file, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f)
    
    def _update_reputation(self, data):
        with codecs.open(self.memory['reputation']['reputation'], 'w', encoding='utf-8') as f:
            json.dump(data, f)
    
    def _get_reputation(self):
        with codecs.open(self.memory['reputation']['reputation'], 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_comeback(self):
        with codecs.open(self.memory['reputation']['comebacks'], 'r', encoding='utf-8') as f:
            comebacks = json.load(f)
            return random.choice(comebacks)

    @glados.Module.command('upvote', '<user>', 'Add reputation to a user')
    async def upvote(self, message, content):
        members, roles, error = self.parse_members_roles(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return
        if message.author in members:
            await self.client.send_message(message.channel, self._get_comeback().format(message.author.name))
            return
        response = []
        reputation = self._get_reputation()
        for member in members:
            new_reputation = reputation.get(member.name, 0) + 1
            reputation[member.name] = new_reputation
            response.append(_reputation_text(member.name, new_reputation))
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
            response.append(_reputation_text(member.name, new_reputation))
        self._update_reputation(reputation)
        await self.client.send_message(message.channel, ', '.join(response))

    @glados.Module.command('reputation', '<user>', 'See a user\'s reputation')
    async def reputation(self, message, content):
        members, roles, error = self.parse_members_roles(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return
        reputation = self._get_reputation()
        response = [_reputation_text(member.name, reputation.get(member.name, 0)) for member in members ]
        await self.client.send_message(message.channel, ', '.join(response))
    
def _reputation_text(name, reputation):
    return '{}\'{} reputation is {}'.format(name, '' if name.endswith('s') else 's', reputation)
