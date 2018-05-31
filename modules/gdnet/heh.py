import re
import asyncio
from time import strptime
from os.path import join, isfile
from os import listdir
from glados import Module, Permissions
from glados.tools.json import load_json, save_json
from lzma import LZMAFile


class Message(object):
    def __init__(self, raw):
        match = re.match('^\[(.*?)\](.*)$', raw)
        items = match.group(2).split(':')
        self.stamp_str = match.group(1)
        self.stamp = strptime(self.stamp_str, '%Y-%m-%d %H:%M:%S')
        self.server = items[0].strip()
        self.channel = items[1].strip('#').strip()
        match = re.match('^(.*)\((\d+)\)$', items[2].strip())  # need to further split author and ID
        self.author = match.group(1)
        self.author_id = match.group(2)
        self.message = items[3].strip()


class Heh(Module):
    def __init__(self, server_inst, full_name):
        super(Heh, self).__init__(server_inst, full_name)
        self.db = None
        self.db_file = join(self.local_data_dir, 'heh')
        self.__load_db()

    @Permissions.spamalot
    @Module.rule('^(.*)$')
    async def record(self, message, args):
        self.__update_db(message.author.name, message.author.id, message.content)
        self.__save_db()
        return ()

    @Module.command('heh', '<user>', 'How many times someone has said the word "heh" (handy for detecting IRC people or edgelords)')
    async def heh(self, message, args):
        users, roles, error = self.parse_members_roles(message, args)
        if error:
            return await self.client.send_message(message.channel, 'Unknown user')
        user = users[0]

        hehs, total = self.__get_stats_of(user.id)
        if hehs == 0:
            return await self.client.send_message(message.channel, 'User {} has never said "heh"'.format(user.name))
        else:
            return await self.client.send_message(message.channel, '{} has said "heh" {} times ({:.3f}%)'.format(
                user.name, hehs, hehs*100.0/total))

    @Module.command('hehstats', '', 'Shows the top users who say "heh" the most (handy for detecting IRC people or edgelords)')
    async def hehstats(self, message, args):
        lines = ['  {: <16} - {} times ({:.3f}%)'.format(author_name, hehs, hehs*100.0/total).ljust(10)
                 for author_name, hehs, total in self.__get_top5()]
        msg = '```Top 5 edgelords\n'
        msg += '\n'.join(lines)
        msg += '```'
        await self.client.send_message(message.channel, msg)

    @Permissions.admin
    @Module.command('hehreload', '', 'Parses all log files in search for "heh"')
    async def heh_reload(self, message, args):
        log_dir = join(self.local_data_dir, 'log')
        files = [join(log_dir, f) for f in listdir(log_dir) if isfile(join(log_dir, f))]
        self.db = {'users': dict()}

        files_processed = 0
        for i, f in enumerate(sorted(files)):
            match = re.match('^.*/chanlog-([0-9]+-[0-9]+-[0-9]+).txt.xz$', f)
            if match is None:
                continue
            print(f)

            try:
                for line in LZMAFile(f, 'r'):
                    # parse the message into its components (author, timestamps, channel, etc.)
                    m = Message(line.decode('utf-8'))
                    self.__update_db(m.author, m.author_id, m.message)
            except EOFError:  # The latest log file may be open
                pass

            # may take a while, yield every so often
            files_processed += 1
            if files_processed % 10 == 0:
                await asyncio.sleep(0)

        self.__save_db()
        await self.client.send_message(message.channel, 'Done!')

    def __load_db(self):
        if isfile(self.db_file):
            self.db = load_json(self.db_file)
        else:
            self.db = {'users': dict()}

    def __save_db(self):
        save_json(self.db_file, self.db)

    def __update_db(self, user_name, user_id, message_content):
        if user_id not in self.db['users']:
            self.db['users'][user_id] = {
                'name': user_name,
                'num msgs': 0,
                'hehs': 0
            }

        self.db['users'][user_id]['num msgs'] += 1
        if re.search(" ?heh", message_content, re.IGNORECASE):
            self.db['users'][user_id]['hehs'] += 1

    def __get_stats_of(self, user_id):
        try:
            user = self.db['users'][user_id]
            return user['hehs'], user['num msgs']
        except KeyError:
            return 0, 0

    def __get_top5(self):
        top5 = list(sorted(self.db['users'].values(), key=lambda x: float(x['hehs']) / x['num msgs'], reverse=True))[:5]
        return [(x['name'], x['hehs'], x['num msgs']) for x in top5]

