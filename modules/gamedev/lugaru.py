import glados
import os
import json
from datetime import datetime, timedelta
from time import strptime, strftime


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
    def get_help_list(self): return [glados.Help('lugaru', '', 'Days since lugaru was mentioned')]

    def setup_memory(self):
        mem = self.get_memory()
        mem['db file'] = os.path.join(self.get_config_dir(), 'lugaru.json')
        mem['db'] = dict()
        self.__load_db()

    def __load_db(self):
        mem = self.get_memory()
        if os.path.isfile(mem['db file']):
            mem['db'] = json.loads(open(mem['db file'], 'r').read())
        if not 'timestamp' in mem['db']:
            mem['db']['timestamp'] = datetime.now().strftime(FORMAT)
        if not 'author' in mem['db']:
            mem['db']['author'] = '(this is the first mention)'
        if not 'record' in mem['db']:
            mem['db']['record'] = 0

    def __save_db(self):
        mem = self.get_memory()
        open(mem['db file'], 'w').write(json.dumps(mem['db']))

    def __get_data(self):
        mem = self.get_memory()
        now = datetime.now()
        last_mentioned = datetime.strptime(mem['db']['timestamp'], FORMAT)
        author = mem['db']['author']
        record = mem['db']['record']
        delta = now - last_mentioned
        if int(record) < delta.days:
            record = delta.days
        return delta, author, record

    # Don't match commands
    @glados.Module.rules('^(?!\.\w+).*lugaru.*$')
    def lugaru_was_mentioned(self, message, match):
        delta, author, record = self.__get_data()
        await self.client.send_message(message.channel, 'Days since `lugaru` was mentioned: :zero: :zero: :zero: :zero: (record was {} day(s) by {})'.format(record, author))

        mem = self.get_memory()
        mem['db']['record'] = delta.days
        mem['db']['timestamp'] = datetime.now().strftime(FORMAT)
        mem['db']['author'] = message.author.name
        self.__save_db()

    @glados.Module.commands('lugaru')
    def lugaru(self, message, args):
        delta, author, record = self.__get_data()
        msg = '`Lugaru` was mentioned {} by {} (current record: {} day(s))'.format(readable_timestamp(delta), author, record)
        await self.client.send_message(message.channel, msg)

