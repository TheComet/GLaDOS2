import glados
import os
import json
from datetime import datetime, timedelta


class Permissions(glados.Permissions):

    def setup_global(self):
        # Create an entry in the global config file with the default command names
        permissions = self.settings.setdefault('permissions', {})
        permissions.setdefault('bot owner', '<please enter your discord ID>')

    def setup_memory(self):
        self.memory['dict'] = dict()
        self.memory['config file'] = os.path.join(self.data_dir, 'permissions.json')
        self.__load_dict()

    def get_help_list(self):
        return [
            glados.Help('modhelp', '', 'Moderator/Admin commands for the bot'),
            glados.Help('modlist', '', 'Displays which users are bot moderators'),
            glados.Help('banlist', '', 'Displays which users are banned'),
            glados.Help('blesslist', '', 'Displays which users are blessed'),
            glados.Help('optoutlist', '', 'Displays which users don\'t want to be logged by the bot')
        ]

    def is_banned(self, member):
        return self.__is_member_still_marked_as(member, 'banned')

    def is_blessed(self, member):
        return self.__is_member_still_marked_as(member, 'blessed')

    def is_moderator(self, member):
        return self.__is_member_still_marked_as(member, 'moderator')

    def is_admin(self, member):
        return self.__is_member_still_marked_as(member, 'admin')

    def is_owner(self, member):
        return self.require_owner(member)

    def require_moderator(self, member):
        if self.require_admin(member):
            return True
        return self.__is_member_still_marked_as(member, 'moderator')

    def require_admin(self, member):
        if self.require_owner(member):
            return True
        return self.__is_member_still_marked_as(member, 'admin')

    def require_owner(self, member):
        if member.id == self.settings['permissions']['bot owner']:
            return True
        return False

    def get_ban_expiry(self, member):
        return self.__get_expiry(member, 'banned')

    @glados.Module.commands('modhelp')
    async def modhelp(self, message, content):
        # If the user was banned, don't announce the help sending
        if self.is_banned(message.author):
            await self.client.send_message(message.channel, "I just PM'd you the help list!")

        await self.client.send_message(message.author,
               "{0}{1} **<user> [hours]** -- Blacklist the specified user from using the bot for the "
               "specified number of hours. The default number of hours is 24. Specifying a value"
               " of 0 will cause the user to be perma-banned. The ban is based on user ID.\n"
               "{0}{2} **<user>** -- Allow a banned user to use the bot again.\n"
               "{0}{3} **<user>** -- Allow the specified user to evade the punishment system. "
               "This allows the user to excessively use the bot without consequences.\n"
               "{0}{4} **<user>** -- Prevents spam from this user by putting him through the punishment system.\n".format(
                   self.settings['commands']['prefix'],
                   'ban',
                   'unban',
                   'bless',
                   'unbless')
        )

    @glados.Module.commands('modlist')
    async def modlist(self, message, content):
        mod_list = list()
        admin_list = list()
        owner = None
        for member in self.current_server.members:
            if member.id in self.memory['dict']['moderator']['IDs']:
                if not member in mod_list:
                    mod_list.append(member)
            if member.id in self.memory['dict']['admin']['IDs']:
                if not member in admin_list:
                    admin_list.append(member)
            if member.id == self.settings['permissions']['bot owner']:
                owner = member

        text = '**Moderators:**\n{}\n**Administrators:**\n{}\n**Owner:** {}'.format(
            '\n'.join(['  + ' + str(x) for x in mod_list]),
            '\n'.join(['  + ' + str(x) for x in admin_list]),
            owner
        )

        await self.client.send_message(message.channel, text)

    @glados.Module.commands('banlist')
    async def banlist(self, message, content):
        banned = list()
        for member in self.current_server.members:
            if member.id in self.settings['banned']:
                expiry_date = self.settings['banned'][member.id]
                if not expiry_date == 'never':
                    expiry_date = dateutil.parser.parse(expiry_date)
                    now = datetime.now()
                    if expiry_date > now:
                        time_to_expiry = expiry_date - now
                        time_to_expiry = '{0:.1f} hour(s)'.format(time_to_expiry.seconds / 3600.0)
                    else:
                        time_to_expiry = '0 hour(s)'
                else:
                    time_to_expiry = 'forever'
                banned.append((member, time_to_expiry))

        if len(banned) > 0:
            text = '**Banned Users**\n{}'.format('\n'.join(['  + ' + x[0].name + ' for {}'.format(x[1]) for x in banned]))
        else:
            text = 'No one is banned.'
        await self.client.send_message(message.channel, text)

    @glados.Module.commands('blesslist')
    async def blesslist(self, message, content):
        blessed = list()
        for member in self.current_server.members:
            if member.id in self.settings['blessed']:
                if not member in blessed:
                    blessed.append(member)

        if len(blessed) > 0:
            text = '**Blessed Users**\n{}'.format('\n'.join(['  + ' + x.name for x in blessed]))
        else:
            text = 'No one is blessed.'
        await self.client.send_message(message.channel, text)

    @glados.Module.commands('optoutlist')
    async def optoutlist(self, message, content):
        optouts = list()
        for member in self.current_server.members:
            if member.id in self.settings['optout']:
                if not member in optouts:
                    optouts.append(member)

        if len(optouts) > 0:
            text = '**Opted-Out Users**\n{}'.format('\n'.join(['  + ' + x.name for x in optouts]))
        else:
            text = 'No one has opted out.'
        await self.client.send_message(message.channel, text)

    @glados.Permissions.moderator
    @glados.Module.commands('ban')
    async def ban_command(self, message, content):
        members, roles, duration, error = self.__parse_members_roles_duration(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return

        # If you are a moderator, then you can't ban admins
        if self.is_moderator(message.author):
            filtered_members = list()
            send_error = False
            for member in members:
                if self.is_admin(member):
                    for role in member.roles:
                        try:
                            roles.remove(role)
                        except ValueError:
                            pass
                    send_error = True
                else:
                    filtered_members.append(member)
            members = filtered_members
            if send_error:
                await self.client.send_message(message.channel, 'Moderators can\'t ban admins')

        await self.client.send_message(message.channel,
                self.__mark_command(members, roles, duration, 'banned'))

    @glados.Permissions.moderator
    @glados.Module.commands('unban')
    async def unban_command(self, message, content):
        members, roles, duration, error = self.__parse_members_roles_duration(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return

        await self.client.send_message(message.channel,
                self.__unmark_command(members, roles, 'banned'))

    @glados.Permissions.moderator
    @glados.Module.commands('bless')
    async def bless_command(self, message, content):
        members, roles, duration, error = self.__parse_members_roles_duration(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return

        await self.client.send_message(message.channel,
                self.__mark_command(members, roles, duration, 'blessed'))

    @glados.Permissions.moderator
    @glados.Module.commands('unbless')
    async def unbless_command(self, message, content):
        members, roles, duration, error = self.__parse_members_roles_duration(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return

        await self.client.send_message(message.channel,
                self.__unmark_command(members, roles, 'blessed'))

    @glados.Permissions.admin
    @glados.Module.commands('mod')
    async def mod_command(self, message, content):
        members, roles, duration, error = self.__parse_members_roles_duration(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return

        await self.client.send_message(message.channel,
                self.__mark_command(members, roles, duration, 'moderator'))

    @glados.Permissions.admin
    @glados.Module.commands('unmod')
    async def unmod_command(self, message, content):
        members, roles, duration, error = self.__parse_members_roles_duration(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return

        await self.client.send_message(message.channel,
                self.__unmark_command(members, roles, 'moderator'))

    @glados.Permissions.owner
    @glados.Module.commands('admin')
    async def admin_command(self, message, content):
        members, roles, duration, error = self.__parse_members_roles_duration(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return

        await self.client.send_message(message.channel,
                self.__mark_command(members, roles, duration, 'admin'))

    @glados.Permissions.owner
    @glados.Module.commands('unadmin')
    async def unadmin_command(self, message, content):
        members, roles, duration, error = self.__parse_members_roles_duration(message, content)
        if error:
            await self.client.send_message(message.channel, error)
            return

        await self.client.send_message(message.channel,
                self.__unmark_command(members, roles, 'admin'))

    def __parse_members_roles_duration(self, message, content):
        if content == '':
            return (), (), 'Invalid syntax. Type `.modhelp` if you need help.'

        # Default duration is 24 hours
        args = content.split()
        if len(args) < 2:
            duration = 24
        else:
            try:
                duration = float(args[-1])
            except ValueError:
                duration = 24

        members, roles, error = self.parse_members_roles(message, content)
        return members, roles, duration, error

    def __mark_command(self, members, roles, duration, key):
        if duration > 0:
            expiry_date = datetime.now() + timedelta(duration / 24.0)
        else:
            expiry_date = 'forever'
        for member in members:
            self.__mark_member_as(member, key, duration_h=duration)
        for role in roles:
            self.__mark_role_as(role.name, key, duration_h=duration)

        # Generate message to send to channel
        users_marked = ', '.join([x.name for x in members])
        roles_marked = ', '.join([x.name for x in roles])
        msg = ''
        if users_marked:
            msg = 'User{} "{}"'.format('s' if len(members) > 1 else '', users_marked)
        if roles_marked:
            if users_marked:
                msg += ' and '
            msg += 'Role{} "{}" '.format('s' if len(roles) > 1 else '', roles_marked)
        msg += ' {} {} until {}'.format(
            'are' if len(members) + len(roles) > 1 else 'is', key, expiry_date)
        return msg

    def __unmark_command(self, members, roles, key):
        unmarked = list()
        for member in members:
            if not self.__is_member_still_marked_as(member, key):
                continue
            self.__unmark_member(member, key)
            unmarked.append(member)
        for role in roles:
            self.__unmark_role(role.name, key)
            unmarked.append(role)

        return '"{}": No longer {}'.format(', '.join(x.mention for x in unmarked), key)

    def __load_dict(self):
        if os.path.isfile(self.memory['config file']):
            self.memory['dict'] = json.loads(open(self.memory['config file']).read())

        # make sure all keys exists
        def add_default(key):
            self.memory['dict'].setdefault(key, {
                'IDs': {},
                'roles': {}
            })
        add_default('banned')
        add_default('blessed')
        add_default('moderator')
        add_default('admin')

    def __save_dict(self):
        with open(self.memory['config file'], 'w') as f:
            s = json.dumps(self.memory['dict'], indent=2, sort_keys=True)
            print(s)
            f.write(s)

    def __get_members_from_string(self, message, user_name):
        # Use mentions instead of looking up the name if possible
        if len(message.mentions) > 0:
            return message.mentions

        user_name = user_name.strip('@').split('#')[0]
        members = list()
        for member in self.current_server.members:
            if member.nick == user_name or member.name == user_name:
                members.append(member)
        if len(members) == 0:
            return 'Error: No member found with the name "{}"'.format(user_name)
        if len(members) > 1:
            return 'Error: Multiple members share the name "{}". Try again by mentioning the user.'.format(user_name)
        return members

    def __is_member_still_marked_as(self, member, key):
        try:
            expiry_dates = [
                ('IDs', member.id, self.memory['dict'][key]['IDs'][member.id])
            ]
        except KeyError:
            member_role_names = set(x.name for x in member.roles)
            key_role_names = set(self.memory['dict'][key]['roles'])
            expiry_dates = [('roles', x, self.memory['dict'][key]['roles'][x])
                            for x in member_role_names.intersection(key_role_names)]
            if len(expiry_dates) == 0:
                return False

        # NOTE: expiry_dates contains a list of tuples, where each tuple is:
        #   (type_key, item_key, expiry_date)
        # This is to match the JSON structure so keys can be deleted easily. The structure is:
        #   key : {
        #     type_key1 : {
        #       item_key1 : expiry_date,
        #       item_key2 : expiry_date
        #     },
        #     type_key2: {
        #       item_key1 : expiry_date
        #       item_key2 : expiry_date
        #     }
        #   }

        expiry_dates_len = len(expiry_dates)
        for type_key, item_key, expiry_date in expiry_dates:
            if expiry_date == 'never':
                continue
            if datetime.now().isoformat() > expiry_date:
                self.memory['dict'][key][type_key].pop(item_key)
                expiry_dates_len -= 1

        if expiry_dates_len < len(expiry_dates):
            self.__save_dict()

        if expiry_dates_len == 0:
            return False
        return True

    def __mark_member_as(self, member, key, duration_h=0):
        if duration_h > 0:
            expiry_date = datetime.now() + timedelta(duration_h / 24.0)
            expiry_date = expiry_date.isoformat()
        else:
            expiry_date = 'never'
        self.memory['dict'][key]['IDs'][member.id] = expiry_date
        self.__save_dict()

    def __mark_role_as(self, role_name, key, duration_h=0):
        if duration_h > 0:
            expiry_date = datetime.now() + timedelta(duration_h / 24.0)
            expiry_date = expiry_date.isoformat()
        else:
            expiry_date = 'never'
        self.memory['dict'][key]['roles'][role_name] = expiry_date
        self.__save_dict()

    def __unmark_member(self, member, key):
        self.memory['dict'][key]['IDs'].pop(member.id, None)
        self.__save_dict()

    def __unmark_role(self, role_name, key):
        self.memory['dict'][key]['roles'].pop(role_name, None)
        self.__save_dict()

    def __get_expiry(self, member, key):
        try:
            return self.memory['dict'][key]['IDs'][member.id]
        except KeyError:
            banned_roles = self.memory['dict']['banned']['roles']
            for role in member.roles:
                expiry = banned_roles.get(role.name, '')
                if expiry:
                    return expiry
        raise RuntimeError('Tried to get expiry on a member that has no expiry')
