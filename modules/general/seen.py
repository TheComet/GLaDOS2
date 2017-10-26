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
    def __init__(self, server_instance, full_name):
        super(Seen, self).__init__(server_instance, full_name)

        self.db = dict()
        self.db_file = os.path.join(self.local_data_dir, 'seen.json')
        self.__load_dict()

    def __load_dict(self):
        if os.path.isfile(self.db_file):
            self.db = json.loads(open(self.db_file).read())
        # make sure all keys exists
        for k, v in self.db.items():
            if not 'author' in v: v['author'] = k
            if not 'channel' in v: v['channel'] = 'unknown_channel'

    def __save_dict(self):
        with open(self.db_file, 'w') as f:
            f.write(json.dumps(self.db))

    @glados.Permissions.spamalot
    @glados.Module.rule('^.*$', ignorecommands=False)
    async def on_message(self, message, match):
        author = message.author.name
        key = author.lower()
        channel = message.channel.name
        msg = message.clean_content
        ts = datetime.now().isoformat()
        self.db[key] = {'author': str(key),
                                    'message': str(msg),
                                    'channel': str(channel),
                                    'timestamp': str(ts)}
        self.__save_dict()
        return ()

    @glados.Module.command('seen', '<user>', 'Find the last message a user wrote, where he wrote it, and what it said')
    async def on_seen(self, message, content):
        if content == "":
            # Count how many users in total have been seen
            await self.client.send_message(message.channel, '{} users have been seen saying at least something.'.format(len(self.db)))
            return

        author = content.strip('@').split('#')[0]
        key = author.lower()
        if key not in self.db:
            if key == 'glados':
                await self.client.send_message(message.channel, '{0} Do you see me? I see you.')
            else:
                await self.client.send_message(message.channel, '{0} has never been seen.'.format(author))
            return

        stamp = get_time(self.db[key]['timestamp'])
        elapsed = datetime.now() - stamp
        await self.client.send_message(message.channel, '{0} was last seen {1} in #{2} saying: "{3}"'.format(
            self.db[key]['author'],
            readable_timestamp(elapsed),
            self.db[key]['channel'],
            self.db[key]['message']
        ))
