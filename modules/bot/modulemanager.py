from glados import Permissions, Module


class ModuleManager(Module):
    @Permissions.admin
    @Module.command('modulelist', '', 'Dumps a list of all modules and which ones are whitelisted/blacklisted')
    async def modulelist(self, message, content):
        strings = ['**List of active modules**']
        strings += sorted(m.full_name for m in self.active_modules)
        strings += ['**List of blacklisted modules**']
        strings += sorted(m.full_name for m in self.blacklisted_modules)
        for msg in self.pack_into_messages(strings):
            await self.client.send_message(message.channel, msg)

    @Permissions.admin
    @Module.command('moduleblack', '<module name> [module name...]', 'Blacklists the specified module(s), thus '
                                                                     'completely disabling them.')
    async def moduleblack(self, message, content):
        blacklist = self.settings['modules']['blacklist']
        modules_already_blacklisted = set(blacklist.setdefault(self.current_server.id, []))
        modules_to_blacklist = set(content.split()) \
            .difference(modules_already_blacklisted) \
            .intersection(m.full_name for m in self.available_modules)

        # Need to update entry in settings.json as well as the set maintained by each module
        blacklist[self.current_server.id] += list(modules_to_blacklist)
        for m in self.available_modules:
            if m.full_name in modules_to_blacklist:
                m.server_blacklist.add(self.current_server.id)

    @Permissions.admin
    @Module.command('modulewhite', '<module name> [module name...]',
                    'Adds the specified module(s) to this server\'s whitelist. This does '
                    'two things: 1) The module will remain available on your server, even if it is removed from the '
                    'default list in the future. 2) If the module was not available, it will be after this command.')
    async def modulewhite(self, message, content):
        blacklist = self.settings['modules']['blacklist']
        modules_currently_blacklisted = blacklist.setdefault(message.server.id, [])
        modules_to_whitelist = set(content.split()) \
            .intersection(modules_currently_blacklisted)

        # Need to update entry in settings.json as well as the set maintained by each module
        blacklist[self.current_server.id] = [x for x in blacklist[self.current_server.id]
                                             if x not in modules_to_whitelist]
        for m in self.available_modules:
            try:
                m.server_blacklist.remove(self.current_server.id)
            except KeyError:
                pass
