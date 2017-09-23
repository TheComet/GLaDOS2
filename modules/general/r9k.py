import glados
import os
import hashlib
import re
import json


class R9K(glados.Module):
    def get_help_list(self):
        return [glados.Help('r9k', '', 'ROBOT9000 tells you how many original comments you\'ve made')]

    def setup_memory(self):
        memory = self.get_memory()

        # Copy active channels from settings file into memory
        memory['channels'] = set()
        for channel_id in self.settings['r9k']['channels']:
            memory['channels'].add(channel_id)

        # directory where r9k stuff is stored
        memory['path'] = os.path.join(self.get_config_dir(), 'r9k')
        if not os.path.exists(memory['path']):
            os.makedirs(memory['path'])

        # load score board, if it exists
        memory['scores file'] = os.path.join(memory['path'], 'scores.json')
        if os.path.isfile(memory['scores file']):
            memory['scores'] = json.loads(open(memory['scores file']).read())
        else:
            memory['scores'] = dict()

        # set up hash tables
        db_file = os.path.join(memory['path'], 'hashes.txt')
        memory['hashes file'] = open(db_file, 'a')
        memory['hashes'] = set()
        for line in open(db_file):
            memory['hashes'].add(line.strip())

    @glados.Module.commands('r9k')
    def send_scores(self, message, users):
        memory = self.get_memory()

        if users == '':
            msg = '**Top 5 most unoriginal users**\n'
            top5 = sorted(memory['scores'].items(), key=lambda kv: kv[1]['score'], reverse=True)[:5]
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
                author = memory['scores'][user_name]
                permille = 1000 * float(author['score']) / float(author['message count'])
                msg = '{0} has been unoriginal {1:.2f}‰ of the time'.format(user_name, permille)
            except KeyError:
                msg = '{} has never been unoriginal'.format(user_name)

        await self.client.send_message(message.channel, msg)

    # matches everything except strings beginning with a ".xxx" to ignore commands
    @glados.Module.rules('^((?!\.\w+).*)$')
    def on_message(self, message, match):
        memory = self.get_memory()

        # Remove anything that is not alphanumeric
        phrase = match.group(1)
        phrase = re.sub('[^A-Za-z0-9]+', '', phrase)
        h = hashlib.sha256(phrase.encode('utf-8')).hexdigest()

        # Create score entry if it doesn't exist
        author = message.author.name
        if author not in memory['scores']:
            memory['scores'][author] = {'score': 0, 'message count': 0}

        # Need total message count for percentual calculation
        memory['scores'][author]['message count'] += 1

        # Check for originality
        if h in memory['hashes']:
            # annoy user, if enabled
            if message.channel.id in memory['channels']:
                phrase = match.group(1)
                if len(phrase) > 40:
                    phrase = phrase[:40] + '...'
                await self.client.send_message(message.channel, '[r9k] The phrase `{}` is unoriginal!'.format(phrase))

            # update scores
            memory['scores'][author]['score'] += 1

        # lol is this really a good idea?
        with open(memory['scores file'], 'w') as f:
            f.write(json.dumps(memory['scores']))

        memory['hashes'].add(h)
        memory['hashes file'].write(h + '\n')

        return tuple()
