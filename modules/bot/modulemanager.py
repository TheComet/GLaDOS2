import glados
import json
from glados import DummyPermissions, Module
from os.path import join, isfile


class ModuleManager(glados.DummyModuleManager):
    def __init__(self, server_instance, full_name):
        super(ModuleManager, self).__init__(server_instance, full_name)

        self.db_file = join(self.local_data_dir, 'modulemanager.json')
        self.db = dict()
        self.__load_db()

    def is_blacklisted(self, mod):
        return True if mod.full_name in self.db['module blacklist'] else False

    @DummyPermissions.admin
    @Module.command('modulelist', '', 'Dumps a list of all modules and which ones are whitelisted/blacklisted')
    async def modulelist(self, message, content):
        strings = ['**List of active modules**']
        strings += sorted(m.full_name for m in self.active_modules)
        strings += ['**List of blacklisted modules**']
        strings += sorted(m.full_name for m in self.blacklisted_modules)
        for msg in self.pack_into_messages(strings):
            await self.client.send_message(message.channel, msg)

    @DummyPermissions.admin
    @Module.command('moduleblack', '<module name> [module name...]', 'Blacklists the specified module(s), thus '
                                                                     'completely disabling them.')
    async def moduleblack(self, message, content):
        blacklist = self.db['module blacklist']
        modules_to_blacklist = set(content.split()) \
            .difference(blacklist) \
            .intersection(m.full_name for m in self.available_modules)

        user_was_retarded = False
        if self.full_name in modules_to_blacklist:
            modules_to_blacklist.remove(self.full_name)
            user_was_retarded = True
            await self.client.send_message(message.channel, 'Blacklisting {} would be fatal... Ignoring'.format(
                self.full_name))

        if len(modules_to_blacklist) == 0:
            if user_was_retarded:
                return  # Already sent a message, not going to send another
            return await self.client.send_message(message.channel, 'Nothing to blacklist!')

        self.db['module blacklist'] = blacklist.union(modules_to_blacklist)
        self.__save_db()

        strings = ['Module(s)'] + list(modules_to_blacklist) + ['were blacklisted']
        for msg in self.pack_into_messages(strings, delimiter=' '):
            await self.client.send_message(message.channel, msg)

    @DummyPermissions.admin
    @Module.command('modulewhite', '<module name> [module name...]',
                    'Adds the specified module(s) to this server\'s whitelist. This does '
                    'two things: 1) The module will remain available on your server, even if it is removed from the '
                    'default list in the future. 2) If the module was not available, it will be after this command.')
    async def modulewhite(self, message, content):
        blacklist = self.db['module blacklist']
        modules_to_whitelist = set(content.split()) \
            .intersection(blacklist)

        if len(modules_to_whitelist) == 0:
            return await self.client.send_message(message.channel, 'Nothing to whitelist!')

        # Need to update entry in db as well as the set maintained by each module
        self.db['module blacklist'] = blacklist.difference(modules_to_whitelist)
        self.__save_db()

        strings = ['Module(s)'] + list(modules_to_whitelist) + ['were whitelisted']
        for msg in self.pack_into_messages(strings, delimiter=' '):
            await self.client.send_message(message.channel, msg)

    def __load_db(self):
        if isfile(self.db_file):
            self.db = json.loads(open(self.db_file).read())

        # make sure all keys exists
        self.db.setdefault('module blacklist', set())
        self.db['module blacklist'] = set(self.db['module blacklist'])

    def __save_db(self):
        with open(self.db_file, 'w') as f:
            self.db['module blacklist'] = list(self.db['module blacklist'])
            s = json.dumps(self.db, indent=2, sort_keys=True)
            f.write(s)
            self.db['module blacklist'] = set(self.db['module blacklist'])
