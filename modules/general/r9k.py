import glados
import os
import hashlib
import re
import json


class R9K(glados.Module):
    def __init__(self, server_instance, full_name):
        super(R9K, self).__init__(server_instance, full_name)

        # Copy active channels from settings file into memory
        self.channels = set()
        for channel_id in self.settings.setdefault('r9k', {}).setdefault('channels', []):
            self.channels.add(channel_id)

        # directory where r9k stuff is stored
        self.path = os.path.join(self.local_data_dir, 'r9k')
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        # load score board, if it exists
        self.score_file = os.path.join(self.path, 'scores.json')
        if os.path.isfile(self.score_file):
            self.scores = json.loads(open(self.score_file).read())
        else:
            self.scores = dict()

        # set up hash tables
        db_file = os.path.join(self.path, 'hashes.txt')
        self.hashes_file = open(db_file, 'a')
        self.hashes = set()
        for line in open(db_file):
            self.hashes.add(line.strip())

    @glados.Module.command('r9k', '', 'ROBOT9000 tells you how many original comments you\'ve made')
    async def send_scores(self, message, users):

        if users == '':
            msg = '**Top 5 most unoriginal users**\n'
            top5 = sorted(self.scores.items(), key=lambda kv: kv[1]['score'], reverse=True)[:5]
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
                author = self.scores[user_name]
                permille = 1000 * float(author['score']) / float(author['message count'])
                msg = '{0} has been unoriginal {1:.2f}‰ of the time'.format(user_name, permille)
            except KeyError:
                msg = '{} has never been unoriginal'.format(user_name)

        await self.client.send_message(message.channel, msg)

    @glados.DummyPermissions.spamalot
    @glados.Module.rule('^(.*)$')
    async def on_message(self, message, match):
        # Remove anything that is not alphanumeric
        phrase = match.group(1)
        phrase = re.sub('[^A-Za-z0-9]+', '', phrase)
        h = hashlib.sha256(phrase.encode('utf-8')).hexdigest()

        # Create score entry if it doesn't exist
        author = message.author.name
        if author not in self.scores:
            self.scores[author] = {'score': 0, 'message count': 0}

        # Need total message count for percentual calculation
        self.scores[author]['message count'] += 1

        # Check for originality
        if h in self.hashes:
            # annoy user, if enabled
            if message.channel.id in self.channels:
                phrase = match.group(1)
                if len(phrase) > 40:
                    phrase = phrase[:40] + '...'
                await self.client.send_message(message.channel, '[r9k] The phrase `{}` is unoriginal!'.format(phrase))

            # update scores
            self.scores[author]['score'] += 1

        # lol is this really a good idea?
        with open(self.score_file, 'w') as f:
            f.write(json.dumps(self.scores))

        self.hashes.add(h)
        self.hashes_file.write(h + '\n')

        return tuple()
