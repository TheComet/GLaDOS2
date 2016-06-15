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


def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


class Seen(glados.Module):

    def __init__(self, settings):
        super(Seen, self).__init__(settings)
        self.__dict = dict()
        self.__config_file = os.path.join(settings['modules']['config path'], 'seen.json')

        self.__load_dict()

    def __load_dict(self):
        if os.path.isfile(self.__config_file):
            self.__dict = json.loads(open(self.__config_file).read())

    def __save_dict(self):
        with open(self.__config_file, 'w') as f:
            f.write(json.dumps(self.__dict))

    @glados.Module.rules('^.*$')
    def on_message(self, client, message, match):
        author = message.author.name
        msg = message.clean_content
        ts = datetime.now().isoformat()
        self.__dict[author] = {'message': str(msg), 'timestamp': str(ts)}
        self.__save_dict()
        return tuple()

    @glados.Module.commands('seen')
    def on_seen(self, client, message, content):
        if content == "":
            yield from client.send_message(message.channel, ".seen <user>")
            return

        author = content.strip('@')
        if not author in self.__dict:
            yield from client.send_message(message.channel, '{0} has never been seen.'.format(author))
            return

        stamp = get_time(self.__dict[author]['timestamp'])
        elapsed = datetime.now() - stamp
        yield from client.send_message(message.channel, '{0} was last seen {1} ago saying: "{2}"'.format(
            author,
            strfdelta(elapsed, '{days} days {hours} hours {minutes} minutes {seconds} seconds'),
            self.__dict[author]['message']
        ))
