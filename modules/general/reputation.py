import glados
import codecs
import json
import os.path
import random

from datetime import date


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
    'daily_limit': 20,
    'override': {},
}


def create_json_file(path, name, data):
    filepath = os.path.join(path, name)
    if not os.path.exists(filepath):
        with codecs.open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)


class Reputation(glados.Module):
    def __init__(self, server_instance, full_name):
        super(Reputation, self).__init__(server_instance, full_name)
        self.rep_dir = os.path.join(self.local_data_dir, 'reputation')
        if not os.path.exists(self.rep_dir):
            os.makedirs(self.rep_dir)
        create_json_file(self.rep_dir, 'reputation.json', {})
        create_json_file(self.rep_dir, 'comebacks.json', COMEBACKS)
        create_json_file(self.rep_dir, 'config.json', DEFAULT_CONFIG)
        self.activity = {}
    
    def _get_file(self, key):
        with codecs.open(os.path.join(self.rep_dir, '{}.json'.format(key)), 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _update_file(self, key, data):
        with codecs.open(os.path.join(self.rep_dir, '{}.json'.format(key)), 'w', encoding='utf-8') as f:
            json.dump(data, f)
    
    def _get_comeback(self):
        return random.choice(self._get_file('comebacks'))

    def _update_activity_limit(self, member, amount=1):
        config = self._get_file('config')
        user_activity = self.activity.get(member.name, { 'votes': 0, 'date': date.today()})
        self.activity[member.name] = user_activity
        if user_activity['date'] < date.today():
            user_activity['date'] = date.today()
            user_activity['votes'] = 0
        user_limit = config['override'].get(member.name, config['daily_limit'])
        if user_activity['votes'] + amount > user_limit:
            raise Exception('Vote limit exceeded. Your limit is {}.'.format(user_limit))
        user_activity['votes'] = user_activity['votes'] + amount
        user_activity['date'] = date.today()

    @glados.Module.command('upvote', '<user>', 'Add reputation to a user')
    async def upvote(self, message, content):
        members, roles, error = self.parse_members_roles(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return
        if message.author in members:
            await self.client.send_message(message.channel, self._get_comeback().format(message.author.name))
            return
        try:
            self._update_activity_limit(message.author, len(members))
        except Exception as e:
            await self.client.send_message(message.author, e)
            return
        response = []
        reputation = self._get_file('reputation')
        for member in members:
            new_reputation = reputation.get(member.name, 0) + 1
            reputation[member.name] = new_reputation
            response.append(_reputation_text(member.name, new_reputation))
        self._update_file('reputation', reputation)
        await self.client.send_message(message.channel, ', '.join(response))

    @glados.Module.command('downvote', '<user>', 'Remove reputation from a user')
    async def downvote(self, message, content):
        members, roles, error = self.parse_members_roles(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return
        try:
            self._update_activity_limit(message.author, len(members))
        except Exception as e:
            await self.client.send_message(message.author, e)
            return
        response = []
        reputation = self._get_file('reputation')
        for member in members:
            new_reputation = reputation.get(member.name, 0) - 1
            reputation[member.name] = new_reputation
            response.append(_reputation_text(member.name, new_reputation))
        self._update_file('reputation', reputation)
        await self.client.send_message(message.channel, ', '.join(response))

    @glados.Module.command('reputation', '<user>', 'See a user\'s reputation')
    async def reputation(self, message, content):
        members, roles, error = self.parse_members_roles(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return
        reputation = self._get_file('reputation')
        response = [_reputation_text(member.name, reputation.get(member.name, 0)) for member in members ]
        await self.client.send_message(message.channel, ', '.join(response))
    
    @glados.Module.command('toprep', '', 'See the five users with most reputation')
    async def toprep(self, message, content):
        reputation = self._get_file('reputation')
        top = sorted(list(reputation.items()), key=lambda x: x[1], reverse=True)[:5]
        response = []
        for member in top:
            response.append('{}: {}'.format(*member))
        await self.client.send_message(message.channel, '\n'.join(response))
    
    @glados.Module.command('bottomrep', '', 'See the five users with least reputation')
    async def bottomrep(self, message, content):
        reputation = self._get_reputation()
        bottom = sorted(list(reputation.items()), key=lambda x: x[1])[:5]
        response = []
        for member in bottom:
            response.append('{}: {}'.format(*member))
        await self.client.send_message(message.channel, '\n'.join(response))
    
    @glados.Module.command('setrep', '<user> <amount>', 'Change the daily votes for a user')
    async def setrep(self, message, content):
        if not self.require_moderator(message.author):
            await self.client.send_message(message.channel, 'Only mods can do this.')
            return
        amount = 0
        try:
            amount = int(content.split()[1])
        except ValueError:
            await self.client.send_message(message.channel, 'Amount should be a number.')
            return
        members, roles, error = self.parse_members_roles(message, content.split()[0])
        if error:
            await self.client.send_message(message.channel, error)
            return
        config = self._get_file('config')
        name = members.pop().name
        config['override'][name] = amount
        self._update_file('config', config)
        await self.client.send_message(message.channel, '{} daily votes set to {}.'.format(name, amount))


def _reputation_text(name, reputation):
    return '{}\'{} reputation is {}'.format(name, '' if name.endswith('s') else 's', reputation)
