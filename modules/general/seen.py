import glados
import os
import json
from datetime import datetime
from datetime import timedelta


def get_time(dt_str):
    dt, _, us = dt_str.partition(".")
    dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
    us = int(us.rstrip("Z"), 10)
    return dt + timedelta(microseconds=us)


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


class Seen(glados.Module):

    def __init__(self, settings):
        super(Seen, self).__init__(settings)
        self.__dict = dict()
        self.__config_file = os.path.join(settings['modules']['config path'], 'seen.json')

        self.__load_dict()

    def __load_dict(self):
        if os.path.isfile(self.__config_file):
            self.__dict = json.loads(open(self.__config_file).read())
        # make sure all keys exists
        for k, v in self.__dict.items():
            if not 'author' in v: v['author'] = k
            if not 'channel' in v: v['channel'] = 'unknown_channel'

    def __save_dict(self):
        with open(self.__config_file, 'w') as f:
            f.write(json.dumps(self.__dict))

    def get_help_list(self):
        return [
            glados.Help('seen', '<user>', 'Find the last message a user wrote, where he wrote it, and what it said')
        ]

    @glados.Module.rules('^.*$')
    def on_message(self, message, match):
        author = message.author.name
        key = author.lower()
        channel = message.channel.name
        msg = message.clean_content
        ts = datetime.now().isoformat()
        self.__dict[key] = {'author': str(author),
                            'message': str(msg),
                            'channel': str(channel),
                            'timestamp': str(ts)}
        self.__save_dict()
        return tuple()

    @glados.Module.commands('seen')
    def on_seen(self, message, content):
        if content == "":
            yield from self.provide_help('seen', message)
            return

        author = content.strip('@').split('#')[0]
        key = author.lower()
        if not key in self.__dict:
            yield from self.client.send_message(message.channel, '{0} has never been seen.'.format(author))
            return

        stamp = get_time(self.__dict[key]['timestamp'])
        elapsed = datetime.now() - stamp
        yield from self.client.send_message(message.channel, '{0} was last seen {1} in #{2} saying: "{3}"'.format(
            self.__dict[key]['author'],
            readable_timestamp(elapsed),
            self.__dict[key]['channel'],
            self.__dict[key]['message']
        ))
