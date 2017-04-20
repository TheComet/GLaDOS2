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

    def setup_memory(self):
        memory = self.get_memory()
        memory['dict'] = dict()
        memory['config file'] = os.path.join(self.get_config_dir(), 'seen.json')

        self.__load_dict()

    def __load_dict(self):
        memory = self.get_memory()
        if os.path.isfile(memory['config file']):
            memory['dict'] = json.loads(open(memory['config file']).read())
        # make sure all keys exists
        for k, v in memory['dict'].items():
            if not 'author' in v: v['author'] = k
            if not 'channel' in v: v['channel'] = 'unknown_channel'

    def __save_dict(self):
        memory = self.get_memory()
        with open(memory['config file'], 'w') as f:
            f.write(json.dumps(memory['dict']))

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
        self.get_memory()['dict'][key] = {'author': str(key),
                            'message': str(msg),
                            'channel': str(channel),
                            'timestamp': str(ts)}
        self.__save_dict()
        return tuple()

    @glados.Module.commands('seen')
    def on_seen(self, message, content):
        memory = self.get_memory()
        if content == "":
            # Count how many users in total have been seen
            yield from self.client.send_message(message.channel, '{} users have been seen saying at least something.'.format(len(memory['dict'])))
            return

        author = content.strip('@').split('#')[0]
        key = author.lower()
        if not key in memory['dict']:
            if key == 'glados':
                yield from self.client.send_message(message.channel, '{0} Do you see me? I see you.')
            else:
                yield from self.client.send_message(message.channel, '{0} has never been seen.'.format(author))
            return

        stamp = get_time(memory['dict'][key]['timestamp'])
        elapsed = datetime.now() - stamp
        yield from self.client.send_message(message.channel, '{0} was last seen {1} in #{2} saying: "{3}"'.format(
            memory['dict'][key]['author'],
            readable_timestamp(elapsed),
            memory['dict'][key]['channel'],
            memory['dict'][key]['message']
        ))
