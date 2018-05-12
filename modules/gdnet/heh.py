import re
from time import strptime
from os.path import join, isfile
from os import listdir
from glados import Module, Permissions
from glados.tools.json import load_json, save_json


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
        self.__update_db(message.content)
        self.__save_db()
        return ()

    @Module.command('heh', '[user]', 'How many times someone has said the word "heh" (handy for detecting IRC people or edgelords)')
    async def heh(self, message, args):
        users, roles, error = self.parse_members_roles(message, args)
        if not error:
            try:
                count = self.db['users'][users[0].id]['num msgs']
                hehs = self.db['users'][users[0].id]['hehs']
            except KeyError:
                return await self.client.send_message(message.channel, 'User {} has never said "heh"'.format(users[0]))
            await self.client.send_message(message.channel, '{} has said "heh" {:.3}% of the time'.format(users[0], 100.0 * hehs / count))
        else:
            pass # TODO
        return ()

    @Permissions.admin
    @Module.command('refreshheh', '', 'Parses all log files in search for "heh"')
    async def refresh_heh(self, message, args):
        log_dir = join(self.local_data_dir, 'log')
        files = [join(log_dir, f) for f in listdir(log_dir) if isfile(join(log_dir, f))]
        self.db = {'users': dict()}

        for i, f in enumerate(sorted(files)):
            match = re.match('^.*/chanlog-([0-9]+-[0-9]+-[0-9]+)$', f)
            if match is None:
                continue
            print(f)

            for line in open(f, 'rb'):
                # parse the message into its components (author, timestamps, channel, etc.)
                m = Message(line.decode('utf-8'))
                self.__update_db(m.message)
        self.__save_db()
        await self.client.send_message(message.channel, 'Done!')

    def __load_db(self):
        if isfile(self.db_file):
            self.db = load_json(self.db_file)
        else:
            self.db = {'users': dict()}

    def __save_db(self):
        save_json(self.db_file, self.db)

    def __update_db(self, user_id):
        try:
            self.db['users'][user_id]['num msgs'] += 1
        except KeyError:
            self.db['users'][user_id]['num msgs'] = 1

        if re.search("\bheh", message.content, re.IGNORECASE):
            try:
                self.db['users'][user_id]['hehs'] += 1
            except KeyError:
                self.db['users'][user_id]['hehs'] = 1

