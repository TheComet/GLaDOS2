import glados
import collections
from datetime import datetime, timedelta

BUFFER_LEN = 5
TIME_THRESHOLD = 2  # If the average time between messages sinks below this (in seconds), the user is kicked

cdfs_server_id = '318450472157577218'
mute_role_id = '322430117760729088'


class AntiSpam(glados.Module):
    def __init__(self):
        super(AntiSpam, self).__init__()
        self.__times = dict()

    def get_help_list(self):
        return tuple()
   
    @glados.Module.rules('^.*$')
    def on_message(self, message, match):
        author = message.author.id
        if not author in self.__times:
            self.__times[author] = collections.deque([datetime.now()], maxlen=BUFFER_LEN)
            return tuple()

        d = self.__times[author]
        d.append(datetime.now())
        if len(d) < BUFFER_LEN:
            return tuple()

        diffs = [d[i] - d[i-1] for i in range(1,len(d))]
        s = sum(x.total_seconds() for x in diffs)
        if s < TIME_THRESHOLD * BUFFER_LEN:
            if message.author.id != '104330175243636736':
                cdfs_server = self.client.get_server(cdfs_server_id)
                roles = [role for role in cdfs_server.roles if role.id == mute_role_id]
                yield from self.client.add_roles(message.author, *roles)
                yield from self.client.send_message(message.channel, '{} you were muted for spamming. PM an admin if you want to complain'.format(message.author.mention))
                #yield from self.client.kick(message.author)
        
        return tuple()
