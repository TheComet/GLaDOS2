import glados
import json
import os
import re


class Sub(glados.Module):

    def setup(self):
        memory = self.get_memory()
        memory['subs file'] = os.path.join(self.get_config_dir(), 'subs.json')
        memory['subs'] = dict()
        memory['regex'] = list()
        memory['timeout'] = dict()

        if os.path.isfile(memory['subs file']):
            glados.log('Loading subscriptions from {}'.format(memory['subs file']))
            memory['subs'] = json.loads(open(memory['subs file']).read())

    def get_help_list(self):
        return [
            glados.Help('sub', '<regex>', 'Get notified when a message matches')
            glados.Help('unsub', '<number>', 'Stop getting notifications. Use .sublist to get the number')
            glados.Help('sublist', '', 'See all of the things you\'ve subscribed to')
        ]

    def __save_subs(self):
        memory = self.get_memory()
        with open(memory['subs file'], 'w') as f:
            f.write(json.dumps(memory['subs']))

    @glados.Module.commands('sub')
    def subscribe(self, message, regex):
        try:
            compiled_regex = re.compile(regex)
        except re.error as e:
            yield from self.client.send_message(message.channel, str(e))
            return

        memory = self.get_memory()
        memory['regex'].append((compiled_regex, message.author))

        if message.author.id not in memory['subs']:
            memory['subs'][message.author.id] = list()
        memory['subs'][message.author.id].append(regex)

        yield from self.client.send_message(message.channel, 'Subscription added!')

    @glados.Module.commands('unsub')
    def unsubscribe(self, message, args):
        memory = self.get_memory()

        if message.author.id not in memory['subs']:
            yield from self.client.send_message(message.channel, 'You have no subscriptions')
            return

        try:
            indices = [int(x) for x in args.split()]
            if any(i > len(memory['subs'][message.author.id]) for i in indices):
                raise ValueError('Out of range')
        except ValueError:
            yield from self.client.send_message(message.channel, 'Invalid parameter!')
            return



    @glados.Module.commands('sublist')
    def list_subscriptions(self, message, args):
        memory = self.get_memory()
        if message.author.id not in memory['subs']:
            yield from self.client.send_message(message.channel, 'You have no subscriptions')
            return

    @glados.Module.rules('^((?!\.\w+).*)$')
    def on_message(self, message, match):
        pass
