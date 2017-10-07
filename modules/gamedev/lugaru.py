import glados
import os
import json
from datetime import datetime


FORMAT = "%Y-%m-%dT%H:%M:%S"


def readable_timestamp(delta):
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)

    ret = ""
    if not days == 0:
        ret += "{} days".format(days)
        ret += " {} hours".format(hours)
        ret += " {} minutes".format(minutes)
        ret += " {} seconds ago".format(seconds)
    elif not hours == 0:
        ret += "{} hours".format(hours)
        ret += " {} minutes".format(minutes)
        ret += " {} seconds ago".format(seconds)
    elif not minutes == 0:
        ret += "{} minutes".format(minutes)
        ret += " {} seconds ago".format(seconds)
    elif not seconds == 0:
        ret += "{} seconds ago".format(seconds)
    else:
        ret += "right now"
    return ret


class Lugaru(glados.Module):

    def setup_memory(self):
        self.memory['db file'] = os.path.join(self.local_data_dir, 'lugaru.json')
        self.memory['db'] = dict()
        self.__load_db()

    def __load_db(self):
        if os.path.isfile(self.memory['db file']):
            self.memory['db'] = json.loads(open(self.memory['db file'], 'r').read())
        if not 'timestamp' in self.memory['db']:
            self.memory['db']['timestamp'] = datetime.now().strftime(FORMAT)
        if not 'author' in self.memory['db']:
            self.memory['db']['author'] = '(this is the first mention)'
        if not 'record' in self.memory['db']:
            self.memory['db']['record'] = 0

    def __save_db(self):
        open(self.memory['db file'], 'w').write(json.dumps(self.memory['db']))

    def __get_data(self):
        now = datetime.now()
        last_mentioned = datetime.strptime(self.memory['db']['timestamp'], FORMAT)
        author = self.memory['db']['author']
        record = self.memory['db']['record']
        delta = now - last_mentioned
        if int(record) < delta.days:
            record = delta.days
        return delta, author, record

    # Don't match commands
    @glados.Module.rule('^(?!\.\w+).*lugaru.*$')
    async def lugaru_was_mentioned(self, message, match):
        delta, author, record = self.__get_data()
        await self.client.send_message(message.channel, 'Days since `lugaru` was mentioned: :zero: :zero: :zero: :zero: (record was {} day(s) by {})'.format(record, author))

        self.memory['db']['record'] = delta.days
        self.memory['db']['timestamp'] = datetime.now().strftime(FORMAT)
        self.memory['db']['author'] = message.author.name
        self.__save_db()

    @glados.Module.command('lugaru', '', 'Days since lugaru was mentioned')
    async def lugaru(self, message, args):
        delta, author, record = self.__get_data()
        msg = '`Lugaru` was mentioned {} by {} (current record: {} day(s))'.format(readable_timestamp(delta), author, record)
        await self.client.send_message(message.channel, msg)
