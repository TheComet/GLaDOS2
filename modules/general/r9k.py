import glados
import os
import hashlib
import re
import json


class R9K(glados.Module):
    def setup_memory(self):
        # Copy active channels from settings file into memory
        self.memory['channels'] = set()
        for channel_id in self.settings.setdefault('r9k', {}).setdefault('channels', []):
            self.memory['channels'].add(channel_id)

        # directory where r9k stuff is stored
        self.memory['path'] = os.path.join(self.local_data_dir, 'r9k')
        if not os.path.exists(self.memory['path']):
            os.makedirs(self.memory['path'])

        # load score board, if it exists
        self.memory['scores file'] = os.path.join(self.memory['path'], 'scores.json')
        if os.path.isfile(self.memory['scores file']):
            self.memory['scores'] = json.loads(open(self.memory['scores file']).read())
        else:
            self.memory['scores'] = dict()

        # set up hash tables
        db_file = os.path.join(self.memory['path'], 'hashes.txt')
        self.memory['hashes file'] = open(db_file, 'a')
        self.memory['hashes'] = set()
        for line in open(db_file):
            self.memory['hashes'].add(line.strip())

    @glados.Module.command('r9k', '', 'ROBOT9000 tells you how many original comments you\'ve made')
    async def send_scores(self, message, users):

        if users == '':
            msg = '**Top 5 most unoriginal users**\n'
            top5 = sorted(self.memory['scores'].items(), key=lambda kv: kv[1]['score'], reverse=True)[:5]
            for author, d in top5:
                permille = 1000 * float(d['score']) / float(d['message count'])
                msg += '  + {0} ({1:.2f}‰)'.format(author, permille)
        else:
            # Mentions have precedence
            if len(message.mentions) > 0:
                user_name = message.mentions[0].name
            else:
                user_name = users.split(' ', 1)[0].strip('@').split('#')[0]
            try:
                author = self.memory['scores'][user_name]
                permille = 1000 * float(author['score']) / float(author['message count'])
                msg = '{0} has been unoriginal {1:.2f}‰ of the time'.format(user_name, permille)
            except KeyError:
                msg = '{} has never been unoriginal'.format(user_name)

        await self.client.send_message(message.channel, msg)

    @glados.Permissions.spamalot
    @glados.Module.rule('^(.*)$')
    async def on_message(self, message, match):
        # Remove anything that is not alphanumeric
        phrase = match.group(1)
        phrase = re.sub('[^A-Za-z0-9]+', '', phrase)
        h = hashlib.sha256(phrase.encode('utf-8')).hexdigest()

        # Create score entry if it doesn't exist
        author = message.author.name
        if author not in self.memory['scores']:
            self.memory['scores'][author] = {'score': 0, 'message count': 0}

        # Need total message count for percentual calculation
        self.memory['scores'][author]['message count'] += 1

        # Check for originality
        if h in self.memory['hashes']:
            # annoy user, if enabled
            if message.channel.id in self.memory['channels']:
                phrase = match.group(1)
                if len(phrase) > 40:
                    phrase = phrase[:40] + '...'
                await self.client.send_message(message.channel, '[r9k] The phrase `{}` is unoriginal!'.format(phrase))

            # update scores
            self.memory['scores'][author]['score'] += 1

        # lol is this really a good idea?
        with open(self.memory['scores file'], 'w') as f:
            f.write(json.dumps(self.memory['scores']))

        self.memory['hashes'].add(h)
        self.memory['hashes file'].write(h + '\n')

        return tuple()
