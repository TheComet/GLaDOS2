# coding=utf-8
"""
remind.py - Sopel Reminder Module
Copyright 2011, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.
http://sopel.chat
"""
import os
import re
import time
import json
import collections
import codecs
import glados
import glados.tools
import asyncio
from datetime import datetime
from glados.tools.time import get_timezone, format_time

try:
    import pytz
except:
    pytz = None

scaling = collections.OrderedDict([
    ('years', 365.25 * 24 * 3600),
    ('year', 365.25 * 24 * 3600),
    ('yrs', 365.25 * 24 * 3600),
    ('y', 365.25 * 24 * 3600),

    ('months', 29.53059 * 24 * 3600),
    ('month', 29.53059 * 24 * 3600),
    ('mo', 29.53059 * 24 * 3600),

    ('weeks', 7 * 24 * 3600),
    ('week', 7 * 24 * 3600),
    ('wks', 7 * 24 * 3600),
    ('wk', 7 * 24 * 3600),
    ('w', 7 * 24 * 3600),

    ('days', 24 * 3600),
    ('day', 24 * 3600),
    ('d', 24 * 3600),

    ('hours', 3600),
    ('hour', 3600),
    ('hrs', 3600),
    ('hr', 3600),
    ('h', 3600),

    ('minutes', 60),
    ('minute', 60),
    ('mins', 60),
    ('min', 60),
    ('m', 60),

    ('seconds', 1),
    ('second', 1),
    ('secs', 1),
    ('sec', 1),
    ('s', 1),
])

periods = '|'.join(scaling.keys())


class Reminder(glados.Module):

    def __init__(self):
        super(Reminder, self).__init__()

    def setup_memory(self):
        self.memory['reminder_file'] = os.path.join(self.data_dir, 'reminders.db')
        self.memory['rdb'] = self.__load_database()

        async def monitor():
            while True:
                await asyncio.sleep(2.5)

                now = int(time.time())
                unixtimes = [int(key) for key in self.memory['rdb']]
                oldtimes = [t for t in unixtimes if t <= now]
                if not oldtimes:
                    continue

                for oldtime in oldtimes:
                    for (channel_id, author_id, message) in self.memory['rdb'][oldtime]:
                        channel = self.client.get_channel(channel_id)
                        author = self.client.get_member(author_id)
                        if channel is None or author is None:
                            continue

                        if message:
                            self.client.send_message(channel, '{} {}'.format(author.mention, message))
                        else:
                            self.client.send_message(channel, '{}!'.format(author.mention))
                    del self.memory['rdb'][oldtime]
                self.__dump_database()

        asyncio.ensure_future(monitor)

    def __load_database(self):
        data = {}
        if os.path.isfile(self.memory['reminder_file']):
            data = json.loads(codecs.open(self.memory['reminder_file'], 'r', encoding='utf-8').read())
        return data

    def __dump_database(self):
        with codecs.open(self.memory['reminder_file'], 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.memory['rdb']))

    @glados.Module.command('in', '<offset> <reminder>', 'Creates a reminder. Example: ".in 3h45m Go to class"')
    async def remind(self, message, args):
        args = args.split(' ', 1)
        if len(args) < 2:
            await self.provide_help('in', message)
            return

        duration = 0
        message = filter(None, re.split('(\d+(?:\.\d+)? ?(?:(?i)' + periods + ')) ?',
                                        args[0])[1:])
        reminder = ''
        stop = False
        for piece in message:
            grp = re.match('(\d+(?:\.\d+)?) ?(.*) ?', piece)
            if grp and not stop:
                length = float(grp.group(1))
                factor = scaling.get(grp.group(2).lower(), 60)
                duration += length * factor
            else:
                reminder = reminder + piece
                stop = True
        if duration == 0:
            await self.client.send_message(message.channel, "Sorry, didn't understand the input.")
            return

        if duration % 1:
            duration = int(duration) + 1
        else:
            duration = int(duration)

        timezone = get_timezone(
            bot.db, bot.config, None, trigger.nick, trigger.sender)
        self.create_reminder(bot, trigger, duration, reminder, timezone)


    @glados.Module.command('at', '<time> <reminder>', 'Creates a reminder. Example: ".at 13:47 Do your homework!"')
    def at(bot, trigger):
        """
        Gives you a reminder at the given time. Takes hh:mm:ssTimezone
        message. Timezone is any timezone Sopel takes elsewhere; the best choices
        are those from the tzdb; a list of valid options is available at
        http://sopel.chat/tz . The seconds and timezone are optional.
        """
        if not trigger.group(2):
            bot.say("No arguments given for reminder command.")
            return NOLIMIT
        if trigger.group(3) and not trigger.group(4):
            bot.say("No message given for reminder.")
            return NOLIMIT
        regex = re.compile(r'(\d+):(\d+)(?::(\d+))?([^\s\d]+)? (.*)')
        match = regex.match(trigger.group(2))
        if not match:
            bot.reply("Sorry, but I didn't understand your input.")
            return NOLIMIT
        hour, minute, second, tz, message = match.groups()
        if not second:
            second = '0'

        if pytz:
            timezone = get_timezone(bot.db, bot.config, tz,
                                    trigger.nick, trigger.sender)
            if not timezone:
                timezone = 'UTC'
            now = datetime.now(pytz.timezone(timezone))
            at_time = datetime(now.year, now.month, now.day,
                               int(hour), int(minute), int(second),
                               tzinfo=now.tzinfo)
            timediff = at_time - now
        else:
            if tz and tz.upper() != 'UTC':
                bot.reply("I don't have timzeone support installed.")
                return NOLIMIT
            now = datetime.now()
            at_time = datetime(now.year, now.month, now.day,
                               int(hour), int(minute), int(second))
            timediff = at_time - now

        duration = timediff.seconds

        if duration < 0:
            duration += 86400
        self.create_reminder(bot, trigger, duration, message, 'UTC')

    def create_reminder(bot, trigger, duration, message, tz):
        t = int(time.time()) + duration
        reminder = (trigger.sender, trigger.nick, message)
        try:
            self.memory['rdb'][t].append(reminder)
        except KeyError:
            self.memory['rdb'][t] = [reminder]

        self.dump_database(bot.rfn, self.memory['rdb'])

        if duration >= 60:
            remind_at = datetime.utcfromtimestamp(t)
            timef = format_time(bot.db, bot.config, tz, trigger.nick,
                                trigger.sender, remind_at)

            bot.reply('Okay, will remind at %s' % timef)
        else:
            bot.reply('Okay, will remind in %s secs' % duration)
