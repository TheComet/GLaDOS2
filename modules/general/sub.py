import glados
import json
import os
import re
from datetime import datetime, timedelta


class Sub(glados.Module):

    def __init__(self):
        super(Sub, self).__init__()
        self.__enabled = True

    def setup_memory(self):
        memory = self.get_memory()
        memory['subs file'] = os.path.join(self.get_config_dir(), 'subs.json')
        memory['subs'] = dict()
        memory['times'] = dict()

        if os.path.isfile(memory['subs file']):
            glados.log('Loading subscriptions from {}'.format(memory['subs file']))
            memory['subs'] = json.loads(open(memory['subs file']).read())

        self.__recompile_regex()

    def __recompile_regex(self):
        memory = self.get_memory()
        memory['regex'] = list()
        for author_id, regexes in memory['subs'].items():
            for regex in regexes:
                try:
                    compiled_regex = re.compile(regex, flags=re.IGNORECASE)
                    memory['regex'].append((compiled_regex, author_id))
                except re.error:
                    pass

    def get_help_list(self):
        return [
            glados.Help('sub', '<regex>', 'Get notified when a message matches the regex. The regex is **case insensitive** and does not have to match the entire message, it searches for substrings (e.g. ".sub (trash can|trashcan)" will match those two phrases). You must be inactive for at least 1 minute before being notified. You cannot notify yourself. A 1 minute cooldown is placed between notifications to prevent spam.'),
            glados.Help('unsub', '<number> [@user]', 'Stop getting notifications. Use .sublist to get the number'),
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
        if len(regex) > 128:
            yield from self.client.send_message(message.channel, 'Limit of 128 characters exceeded!')
            return

        try:
            compiled_regex = re.compile(regex, flags=re.IGNORECASE)
        except re.error as e:
            yield from self.client.send_message(message.channel, str(e))
            return

        memory = self.get_memory()

        if message.author.id not in memory['subs']:
            memory['subs'][message.author.id] = list()
        if len(memory['subs'][message.author.id]) >= 15:
            yield from self.client.send_message(message.channel, 'Limit of 15 rules exceeded!')
            return

        memory['subs'][message.author.id].append(regex)
        memory['regex'].append((compiled_regex, message.author))
        self.__save_subs()

        yield from self.client.send_message(message.channel, 'Subscription added!')

    @glados.Module.commands('unsub')
    def unsubscribe(self, message, args):
        if args == '':
            yield from self.provide_help('unsub', message)
            return

        if len(message.mentions) > 0:
            is_mod = message.author.id in self.settings['moderators']['IDs'] or \
                     len(set(x.name for x in message.author.roles).intersection(
                         set(self.settings['moderators']['roles']))) > 0
            if not is_mod and not message.author.id in self.settings['admins']['IDs']:
                yield from self.client.send_message(message.channel, 'Only botmods can delete subscriptions from other users')
                return ()

            member = message.mentions[0]
            args = ' '.join(args.split()[:-1])  # remove name from args list
        else:
            member = message.author

        memory = self.get_memory()
        if member.id not in memory['subs']:
            yield from self.client.send_message(message.channel, '{} has no subscriptions'.format(member.name))
            return

        try:
            indices = [int(x) for x in args.split()]
            if any(i > len(memory['subs'][message.author.id]) or i < 1 for i in indices):
                raise ValueError('Out of range')
        except ValueError:
            yield from self.client.send_message(message.channel, 'Invalid parameter! (Is it a number?)')
            return

        memory['subs'][member.id] = [x for i, x in enumerate(memory['subs'][member.id])
                                             if i+1 not in indices]
        if len(memory['subs'][member.id]) == 0:
            del memory['subs'][member.id]
        self.__recompile_regex()
        self.__save_subs()

        yield from self.client.send_message(message.channel, 'Unsubscribed from {}'.format(', '.join(str(x) for x in indices)))

    @glados.Module.commands('subs')
    def toggle_subscription_feature(self, message, args):
        is_mod = message.author.id in self.settings['moderators']['IDs'] or \
                 len(set(x.name for x in message.author.roles).intersection(
                     set(self.settings['moderators']['roles']))) > 0
        if not is_mod and not message.author.id in self.settings['admins']['IDs']:
            return tuple()

        self.__enabled = not self.__enabled
        msg = 'enabled' if self.__enabled else 'disabled'
        yield from self.client.send_message(message.channel, 'Subscription system {}'.format(msg))

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
                member = None
                for m in self.client.get_all_members():
                    if m.name == user_name:
                        member = m
                        break
                if member is None:
                    yield from self.client.send_message(message.channel, 'User "{}" not found'.format(user_name))
                    return

        memory = self.get_memory()
        if member.id not in memory['subs']:
            yield from self.client.send_message(message.channel, 'User "{}" has no subscriptions'.format(member.name))
            return

        msg = '{} is subscribed to\n'.format(member.name)
        for i, regex in enumerate(memory['subs'][member.id]):
            msg += '  {}. `{}`'.format(i+1, regex)
        yield from self.client.send_message(message.channel, msg)

    @glados.Module.rules('^((?!\.\w+).*)$')
    def on_message(self, message, match):
        if not self.__enabled:
            return tuple()

        memory = self.get_memory()

        # Reset timer if user just made a message
        # Doing it here has the nice side effect of making it impossible to mention yourself
        memory['times'][message.author.id] = datetime.now()

        # buffer all mentions, in case multiple people are mentioned (to avoid spamming chat)
        msg = ''

        members_to_remove = list()

        for i, tup in enumerate(memory['regex']):
            regex, subscribed_author = tup[0], tup[1]
            match = regex.search(message.content)
            if match is None:
                continue

            # may need to retrieve the author (this doesn't happen when first loading from JSON)
            if isinstance(subscribed_author, str):
                for member in self.client.get_all_members():
                    if member.id == subscribed_author:
                        subscribed_author = member
                        memory['regex'][i] = (regex, member)
                if isinstance(subscribed_author, str):
                    # failed at getting member, remove all settings (fuck you!)
                    members_to_remove.append(subscribed_author)
                    continue

            # Only perform the mention if enough time has passed
            dt = timedelta(hours=24)  # larger than below, in case time stamp doesn't exist yet
            if subscribed_author.id in memory['times']:
                dt = datetime.now() - memory['times'][subscribed_author.id]
            if dt > timedelta(minutes=1):
                # Make sure the member is even still part of the server (thanks Helper...)
                if any(member.id == subscribed_author.id for member in self.client.get_all_members()):
                    msg += ' {} (`{}`)'.format(subscribed_author.mention, regex.pattern)
                    memory['times'][subscribed_author.id] = datetime.now()
                else:
                    # Remove all settings entirely (fuck you!)
                    members_to_remove.append(subscribed_author.id)

        if msg != '':
            yield from self.client.send_message(message.channel, '[sub]{}'.format(msg))

        for member_id in members_to_remove:
            try:
                del memory['subs'][member_id]
            except KeyError:
                pass
        if len(members_to_remove) > 0:
            self.__save_subs()
            self.__recompile_regex()

        return tuple()
