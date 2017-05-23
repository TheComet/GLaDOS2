import glados
import os
import enchant
import hashlib
import re


class R9K(glados.Module):
    def get_help_list(self):
        return [glados.Help('r9k', '', 'Enables/Disables ROBOT9000 for the channel you type this in')]

    def setup_memory(self):
        memory = self.get_memory()

        # Copy active channels from settings file into memory
        memory['channels'] = set()
        for channel_id in self.settings['r9k']['channels']:
            memory['channels'].add(channel_id)

        db_file = os.path.join(self.get_config_dir(), 'r9k.txt')
        memory['db file'] = open(db_file, 'a')
        memory['db'] = set()
        for line in open(db_file):
            memory['db'].add(line.strip())

        memory['dictionaries'] = [
            enchant.Dict('en_US'),
            enchant.Dict('en_GB')
        ]

    @glados.Module.commands('r9k')
    def toggle(self, message, args):
        # Must be an admin
        if message.author.id not in self.settings['admins']['IDs']:
            yield from self.client.send_message(message.channel, 'You must be an admin to run this command')
            return

        memory = self.get_memory()
        if message.channel.id not in memory['channels']:
            memory['channels'].add(message.channel.id)
            enabled = True
        else:
            memory['channels'].remove(message.channel.id)
            enabled = False

        msg = ('disabled', 'enabled')
        yield from self.client.send_message(message.channel, 'ROBOT9000 {}.'.format(msg[enabled]))

    # matches everything except strings beginning with a ".xxx" to ignore commands
    @glados.Module.rules('^((?!\.\w+).*)$')
    def on_message(self, message, match):
        memory = self.get_memory()

        # Remove anything that is not [a-z][A-Z]_
        phrase = match.group(1)
        phrase = re.sub('[^A-Za-z0-9]+', '', phrase)
        h = hashlib.sha256(phrase.encode('utf-8')).hexdigest()

        # Check for originality
        if message.channel.id in memory['channels'] and h in memory['db']:
            phrase = match.group(1)
            if len(phrase) > 40:
                phrase = phrase[:40] + '...'
            yield from self.client.send_message(message.channel, '[r9k] The phrase `{}` is unoriginal!'.format(phrase))
            return

        memory['db'].add(h)
        memory['db file'].write(h + '\n')
        return tuple()
