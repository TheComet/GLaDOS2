import glados
import discord
import json
import os
import errno
import signal
import re
from datetime import datetime, timedelta
from functools import wraps


class TimeoutError(Exception):
    pass


def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.setitimer(signal.ITIMER_REAL,seconds) #used timer instead of alarm
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        return wraps(func)(wrapper)
    return decorator


@timeout(0.5)
def timeout_match(regex, message):
    return regex.search(message)


class Sub(glados.Module):
    def __init__(self, server_instance, full_name):
        super(Sub, self).__init__(server_instance, full_name)

        self.subs_file = os.path.join(self.local_data_dir, 'subs.json')
        self.subs = dict()
        self.items = dict()

        if os.path.isfile(self.subs_file):
            glados.log('Loading subscriptions from {}'.format(self.subs_file))
            self.subs = json.loads(open(self.subs_file).read())

        self.__recompile_regex()

    def __recompile_regex(self):
        self.regex = list()
        for author_id, regexes in self.subs.items():
            for regex in regexes:
                try:
                    compiled_regex = re.compile(regex, flags=re.IGNORECASE)
                    self.regex.append((compiled_regex, author_id))
                except re.error:
                    pass

    def __save_subs(self):
        with open(self.subs_file, 'w') as f:
            f.write(json.dumps(self.subs))

    @glados.Module.command('sub', '<regex>', 'Get notified when a message matches the regex. The regex is **case '
                           'insensitive** and does not have to match the entire message, it searches for substrings '
                           '(e.g. ".sub (trash can|trashcan)" will match those two phrases). You must be inactive for '
                           'at least 1 minutes before being notified. You cannot notify yourself. A 1 minute cooldown '
                           'is placed between notifications to prevent spam.')
    async def subscribe(self, message, regex):
        if regex == '':
            await self.provide_help('sub', message)
            return
        if len(regex) > 128:
            await self.client.send_message(message.channel, 'Limit of 128 characters exceeded!')
            return

        if len(regex) < 5:
            regex = r'\b' + regex + r'\b'

        try:
            compiled_regex = re.compile(regex, flags=re.IGNORECASE)
        except re.error as e:
            await self.client.send_message(message.channel, str(e))
            return

        if message.author.id not in self.subs:
            self.subs[message.author.id] = list()
        if len(self.subs[message.author.id]) >= 15:
            await self.client.send_message(message.channel, 'Limit of 15 rules exceeded!')
            return

        self.subs[message.author.id].append(regex)
        self.regex.append((compiled_regex, message.author))
        self.__save_subs()

        await self.client.send_message(message.channel, '{} added subscription #{} (``{}``)'.format(message.author.name, len(self.subs[message.author.id]), regex))

    @glados.Module.command('unsub', '<number> [user]', 'Stop getting notifications. Use .sublist to get the number')
    async def unsubscribe(self, message, args):
        if args == '':
            await self.provide_help('unsub', message)
            return

        if message.author.id not in self.subs:
            await self.client.send_message(message.channel, '{} has no subscriptions'.format(message.author.name))
            return

        try:
            indices = [int(x) for x in args.split()]
            if any(i > len(self.subs[message.author.id]) or i < 1 for i in indices):
                raise ValueError('Out of range')
        except ValueError:
            await self.client.send_message(message.channel, 'Invalid parameter! (Is it a number?)')
            return

        self.subs[message.author.id] = [x for i, x in enumerate(self.subs[message.author.id])
                                             if i+1 not in indices]
        if len(self.subs[message.author.id]) == 0:
            del self.subs[message.author.id]
        self.__recompile_regex()
        self.__save_subs()

        await self.client.send_message(message.channel, '{} unsubscribed from {}'.format(message.author.name, ', '.join(str(x) for x in indices)))

    @glados.Module.command('sublist', '[user]', 'See all of the things you\'ve subscribed to')
    async def list_subscriptions(self, message, user):
        if user == '':
            member = message.author
        else:
            # Mentions have precedence
            if len(message.mentions) > 0:
                member = message.mentions[0]
            else:
                user_name = user.strip('@').split('#')[0]
                member = None
                for m in self.server.members:
                    if m.name == user_name:
                        member = m
                        break
                if member is None:
                    await self.client.send_message(message.channel, 'User "{}" not found'.format(user_name))
                    return

        if member.id not in self.subs:
            await self.client.send_message(message.channel, 'User "{}" has no subscriptions'.format(member.name))
            return

        msg = '{} is subscribed to\n'.format(member.name)
        for i, regex in enumerate(self.subs[member.id]):
            msg += '  #{} `{}`'.format(i+1, regex)
        await self.client.send_message(message.channel, msg)

    @glados.Permissions.spamalot
    @glados.Module.rule('^(.*)$')
    async def on_message(self, message, match):
        # Reset timer if user just made a message
        # Doing it here has the nice side effect of making it impossible to mention yourself
        self.items[message.author.id] = datetime.now()

        # buffer all mentions, in case multiple people are mentioned (to avoid spamming chat)
        msg = ''

        members_to_remove = list()

        for i, tup in enumerate(self.regex):
            regex, subscribed_author = tup[0], tup[1]

            # may need to retrieve the author (this doesn't happen when first loading from JSON)
            if isinstance(subscribed_author, str):
                for member in self.server.members:
                    if member.id == subscribed_author:
                        subscribed_author = member
                        self.regex[i] = (regex, member)
                if isinstance(subscribed_author, str):
                    # failed at getting member, remove all settings (fuck you!)
                    members_to_remove.append(subscribed_author)
                    continue

            # Do match, with timeout
            try:
                match = timeout_match(regex, message.content)
            except TimeoutError:
                members_to_remove.append(subscribed_author.id)
                await self.client.send_message(message.channel, 'Shit regex detected, removing sublist of {}'.format(subscribed_author.name))
                continue
            if match is None:
                continue

            # Only perform the mention if enough time has passed
            dt = timedelta(hours=24)  # larger than below, in case time stamp doesn't exist yet
            if subscribed_author.id in self.items:
                dt = datetime.now() - self.items[subscribed_author.id]
            if dt > timedelta(minutes=1):
                # Make sure the member is even still part of the server (thanks Helper...)
                if any(member.id == subscribed_author.id for member in self.server.members):
                    pattern = regex.pattern
                    if len(pattern) > 30:
                        pattern = pattern[:30] + '...'
                    # Thanks GTE (blocked the bot, which causes this to throw an exception)
                    try:
                        await self.client.send_message(subscribed_author, '[sub][{}][{}] (``{}``) ```{}: {}```'.format(message.server.name, message.channel.name, pattern, message.author.name, message.content))
                        self.items[subscribed_author.id] = datetime.now()
                    except discord.Forbidden as e:
                        await self.client.send_message(message.channel, '{} I am removing all of your subscriptions, because you blocked me :('.format(subscribed_author.mention))
                        members_to_remove.append(subscribed_author.id)
                else:
                    # Remove all settings entirely (fuck you!)
                    members_to_remove.append(subscribed_author.id)

        for member_id in members_to_remove:
            try:
                del self.subs[member_id]
            except KeyError:
                pass
        if len(members_to_remove) > 0:
            self.__save_subs()
            self.__recompile_regex()

        return tuple()
