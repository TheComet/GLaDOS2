import glados
import json
import os
import re
from datetime import datetime, timedelta


class Sub(glados.Module):

    def setup_memory(self):
        memory = self.get_memory()
        memory['subs file'] = os.path.join(self.get_config_dir(), 'subs.json')
        memory['subs'] = dict()
        memory['regex'] = list()
        memory['times'] = dict()

        if os.path.isfile(memory['subs file']):
            glados.log('Loading subscriptions from {}'.format(memory['subs file']))
            memory['subs'] = json.loads(open(memory['subs file']).read())

        # pre-compile regex
        for author_id, regexes in memory['subs'].items():
            for regex in regexes:
                try:
                    compiled_regex = re.compile(regex)
                    memory['regex'].append((compiled_regex, author_id))
                except re.error:
                    pass

    def get_help_list(self):
        return [
            glados.Help('sub', '<regex>', 'Get notified when a message matches'),
            glados.Help('unsub', '<number>', 'Stop getting notifications. Use .sublist to get the number'),
            glados.Help('sublist', '', 'See all of the things you\'ve subscribed to')
        ]

    def __save_subs(self):
        memory = self.get_memory()
        with open(memory['subs file'], 'w') as f:
            f.write(json.dumps(memory['subs']))

    @glados.Module.commands('sub')
    def subscribe(self, message, regex):
        if regex == '':
            yield from self.provide_help('sub', message)
            return

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
        self.__save_subs()

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

        memory['subs'][message.author.id] = [x for i, x in enumerate(memory['subs'][message.author.id])
                                             if i+1 not in indices]
        if len(memory['subs'][message.author.id]) == 0:
            del memory['subs'][message.author.id]
        self.__save_subs()

        yield from self.client.send_message(message.channel, 'Unsubscribed from {}'.format(', '.join(str(x) for x in indices)))

    @glados.Module.commands('sublist')
    def list_subscriptions(self, message, user):
        if user == '':
            member = message.author
        else:
            # Mentions have precedence
            if len(message.mentions) > 0:
                member = message.mentions[0]
            else:
                user_name = user.strip('@').split('#')[0]
                member = self.client.get_member_named(user_name)
                if member is None:
                    yield from self.client.send_message(message.channel, 'User "{}" not found'.format(user_name))
                    return

        memory = self.get_memory()
        if member.id not in memory['subs']:
            yield from self.client.send_message(message.channel, 'User "{}" has no subscriptions'.format(member.name))
            return

        msg = '{} is subscribed to'.format(member.name)
        for i, regex in enumerate(memory['subs'][member.id]):
            msg += '\n  {}. `{}`'.format(i+1, regex)
        yield from self.client.send_message(message.channel, msg)

    @glados.Module.rules('^((?!\.\w+).*)$')
    def on_message(self, message, match):
        memory = self.get_memory()

        # Reset timer if user just made a message
        # Doing it here has the nice side effect of making it impossible to mention yourself
        memory['times'][message.author.id] = datetime.now()

        for i, tup in enumerate(memory['regex']):
            regex, subscribed_author = tup[0], tup[1]
            match = regex.search(message.clean_content)
            if match is None:
                continue

            # may need to retrieve the author (this doesn't happen when first loading from JSON)
            if isinstance(subscribed_author, str):
                for member in self.client.get_all_members():
                    if member.id == subscribed_author:
                        subscribed_author = member
                        memory['regex'][i] = (regex, member)
                if isinstance(subscribed_author, str):
                    continue  # failed at getting member

            # Only perform the mention if enough time has passed
            dt = timedelta(hours=24)  # larger than below, in case time stamp doesn't exist yet
            if subscribed_author.id in memory['times']:
                dt = datetime.now() - memory['times'][subscribed_author.id]
            if dt > timedelta(minutes=5):
                yield from self.client.send_message(message.channel, '[sub] {}'.format(subscribed_author.mention))
            memory['times'][subscribed_author] = datetime.now()

        return tuple()
