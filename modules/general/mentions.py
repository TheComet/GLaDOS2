import glados
import os.path
import codecs
import json
from datetime import datetime
import dateutil.parser


def strip_timestamp_and_name(msg):
    try:
        dateutil.parser.parse(msg[:19])
    except TypeError:
        return msg
    except ValueError:
        return msg

    return msg[19:].split(':', 1)[1].strip()


def get_timestamp(msg):
    try:
        stamp = dateutil.parser.parse(msg[:19])
    except TypeError:
        return None
    except ValueError:
        return None

    return stamp


def get_author(msg):
    try:
        dateutil.parser.parse(msg[:19])
    except TypeError:
        return None
    except ValueError:
        return None

    return msg[19:].split(':', 1)[0]


class Mentions(glados.Module):
    def setup_memory(self):
        mentions_data_path = os.path.join(self.data_dir, 'mentions')
        if not os.path.exists(mentions_data_path):
            os.makedirs(mentions_data_path)

        self.memory['log file'] = os.path.join(mentions_data_path, 'mentions.txt')
        self.memory['seen file'] = os.path.join(mentions_data_path, 'seen_timestamps.json')
        self.memory['last seen'] = dict()
        self.__load_seen_timestamps()

    def __load_seen_timestamps(self):
        glados.log('loading seen timestamps for .mentions')
        if os.path.isfile(self.memory['seen file']):
            self.memory['last seen'] = json.loads(open(self.memory['seen file']).read())

    def __save_seen_timestamps(self):
        with open(self.memory['seen file'], 'w') as f:
            f.write(json.dumps(self.memory['last seen']))

    @glados.Permissions.spamalot
    @glados.Module.rule('^((?!\.\w+).*)$')
    def record(self, message, match):
        # If user has opted out, don't log
        if message.author.id in self.settings['optout']:
            return ()

        with codecs.open(self.memory['log file'], 'a', encoding='utf-8') as f:
            f.write(datetime.now().isoformat()[:19] + "  " + message.author.name + ": " + message.clean_content + "\n")

        author = message.author.name
        key = author.lower()
        self.memory['last seen'][key] = datetime.now().isoformat()[:19]  # don't need microseconds
        self.__save_seen_timestamps()

        return tuple()

    @glados.Module.command('mentions', '[num]', 'Returns all messages in which you were mentioned since you were last '
                           'seen. If you provide a number, it will return the last [num] messages instead.')
    async def on_seen(self, message, arg):
        glados.log('Looking for mentions for author {}'.format(message.author.name))

        try:
            num = int(arg)
        except ValueError:
            num = 0

        max_num = 5
        mentions = list()
        author = message.author.name
        key = author.lower()

        if num > max_num:
            await self.client.send_message(message.channel, 'Please, don\'t be an idiot')
            return

        mentions_file = codecs.open(self.memory['log file'], 'r', encoding='utf-8')
        lines = mentions_file.readlines()
        mentions_file.close()

        if num == 0:

            if key not in self.memory['last seen']:
                await self.client.send_message(message.channel, '{0} has never been mentioned.'.format(author))
                return

            last_seen = dateutil.parser.parse(self.memory['last seen'][key])
            for msg in reversed(lines):
                stamp = get_timestamp(msg)
                if stamp is None:
                    continue
                if stamp < last_seen:  # no more new messages
                    break
                if key in strip_timestamp_and_name(msg).lower():
                    mentions.append(msg)
        else:

            for msg in reversed(lines):
                if key in strip_timestamp_and_name(msg).lower():
                    mentions.append(msg)
                    num -= 1
                if num == 0:
                    break

        if len(mentions) == 0:
            await self.client.send_message(message.channel, 'No one mentioned you.')
            return

        response = list()
        for msg in mentions:
            author = get_author(msg)
            if author is None:
                author = ''
            else:
                author = '**' + author + '**: '

            response.append(author + strip_timestamp_and_name(msg))

        await self.client.send_message(message.channel, '\n'.join(response))
