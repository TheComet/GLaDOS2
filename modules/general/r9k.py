import glados
import os
import hashlib
import re
import json
import asyncio


class R9K(glados.Module):
    def get_help_list(self):
        return [glados.Help('r9k', '', 'Enables/Disables ROBOT9000 for the channel you type this in')]

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
    def send_scores(self, message, args):
        memory = self.get_memory()
        msg = '**Top 5 most unoriginal users**\n'
        top5 = sorted(memory['scores'].items(), key=lambda kv: kv[1]['score'])[:5]
        for author, d in top5:
            msg += '  + {} ({})'.format(author, d['score'])

        yield from self.client.send_message(message.channel, msg)

    # matches everything except strings beginning with a ".xxx" to ignore commands
    @glados.Module.rules('^((?!\.\w+).*)$')
    def on_message(self, message, match):
        memory = self.get_memory()

        # Remove anything that is not alphanumeric
        phrase = match.group(1)
        phrase = re.sub('[^A-Za-z0-9]+', '', phrase)
        h = hashlib.sha256(phrase.encode('utf-8')).hexdigest()

        # Check for originality
        if h in memory['hashes']:
            # annoy user, if enabled
            if message.channel.id in memory['channels']:
                phrase = match.group(1)
                if len(phrase) > 40:
                    phrase = phrase[:40] + '...'
                yield from self.client.send_message(message.channel, '[r9k] The phrase `{}` is unoriginal!'.format(phrase))

            # update scores
            author = message.author.name
            if author not in memory['scores']:
                memory['scores'][author] = {'score': 0}
            memory['scores'][author]['score'] += 1

            with open(memory['scores file'], 'w') as f:
                f.write(json.dumps(memory['scores']))

        memory['hashes'].add(h)
        memory['hashes file'].write(h + '\n')

        return tuple()
