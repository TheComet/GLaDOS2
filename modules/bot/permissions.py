import glados
import os
import json
from datetime import datetime, timedelta


class Permissions(glados.Permissions):

    def setup_memory(self):
        memory = self.get_memory()
        memory['dict'] = dict()
        memory['config file'] = os.path.join(self.get_config_dir(), 'permissions.json')
        self.__load_dict()

    def is_banned(self, member):
        memory = self.get_memory()
        expiry_date = memory['dict']['banned'].get(member.id, '0')
        if expiry_date == 'never':
            return True

        if datetime.now().isoformat() > expiry_date:
            self.unban(member)
            return False

        return True

    def is_blessed(self, member):
        return False

    def is_moderator(self, member):
        memory = self.get_memory()
        if member.id in memory['dict']['moderators']['IDs']:
            return True
        member_role_names = set(x.name for x in member.roles)
        moderator_role_names = set(memory['dict']['moderators']['roles'])
        if len(member_role_names.intersection(moderator_role_names)) > 0:
            return True

    def is_admin(self, member):
        memory = self.get_memory()
        if member.id in memory['dict']['admins']['IDs']:
            return True
        member_role_names = set(x.name for x in member.roles)
        admin_role_names = set(memory['dict']['admins']['roles'])
        if len(member_role_names.intersection(admin_role_names)) > 0:
            return True

    @glados.Module.commands('ban')
    async def ban(self, message, content):
        if not self.is_moderator(message.author) and not self.is_admin(message.author):
            return ()  # TODO

        if content == '':
            await self.client.send_message(message.channel, 'Invalid syntax. Type `.modhelp` if you need help.')
            return

        args = content.split()
        about_to_be_banned = args[0]

        # If result is a string, then it is an error message.
        about_to_be_banned = self.__get_members_from_string(message, about_to_be_banned)
        if isinstance(about_to_be_banned, str):
            await self.client.send_message(message.channel, about_to_be_banned)
            return

        # If you are a moderator, then you can't ban admins
        if self.is_moderator(message.author):
            filtered_bans = list()
            send_error = False
            for member in about_to_be_banned:
                if self.is_admin(member):
                    send_error = True
                else:
                    filtered_bans.append(member)
            about_to_be_banned = filtered_bans
            if send_error:
                await self.client.send_message(message.channel, 'Moderators can\'t ban admins')

        if len(about_to_be_banned) == 0:
            await self.client.send_message(message.channel, 'No users specified!')
            return

        # Default ban length is 24 hours
        if len(args) < 2:
            hours = 24
        else:
            try:
                hours = float(args[-1])
            except ValueError:
                hours = 24

        memory = self.get_memory()
        if hours > 0:
            expiry_date = datetime.now() + timedelta(hours / 24.0)
            for member in about_to_be_banned:
                memory['dict']['banned'][member.id] = expiry_date.isoformat()
        else:
            for member in about_to_be_banned:
                memory['dict']['banned'][member.id] = 'never'
            expiry_date = 'forever'
        self.__save_dict()

        users_banned = ', '.join([x.name for x in about_to_be_banned])
        await self.client.send_message(message.channel, 'User(s) "{}" is banned from using this bot until {}'.format(users_banned, expiry_date))

    @glados.Module.commands('unban')
    async def unban_command(self, message, content):
        if not self.is_moderator(message.author) and not self.is_admin(message.author):
            return ()  # TODO

        if content == '':
            await self.client.send_message(message.channel, 'Invalid syntax. Type `.modhelp` if you need help.')
            return

        # If result is a string, then it is an error message.
        args = content.split()[0]
        about_to_be_unbanned = self.__get_members_from_string(message, args)
        if isinstance(about_to_be_unbanned, str):
            await self.client.send_message(message.channel, about_to_be_unbanned)
            return

        memory = self.get_memory()
        for member in about_to_be_unbanned:
            if member.id not in memory['dict']['banned']:
                await self.client.send_message(message.channel, 'User "{}" isn\'t banned'.format(member))
            else:
                self.unban(member)
                await self.client.send_message(message.channel, 'Unbanned user "{}"'.format(member))

    def unban(self, member):
        memory = self.get_memory()
        memory['dict']['banned'].pop(member.id, None)
        self.__save_dict()

    def bless(self, member):
        pass

    def unbless(self, member):
        pass

    def get_ban_expiry(self, member):
        memory = self.get_memory()
        return memory['dict']['banned'][member.id]

    def __load_dict(self):
        memory = self.get_memory()
        if os.path.isfile(memory['config file']):
            memory['dict'] = json.loads(open(memory['config file']).read())

        # make sure all keys exists
        memory['dict'].setdefault('banned', {})
        memory['dict'].setdefault('blessed', [])
        memory['dict'].setdefault('moderators', {
            'IDs': [],
            'roles': []
        })
        memory['dict'].setdefault('admins', {
            'IDs': [],
            'roles': []
        })

    def __save_dict(self):
        memory = self.get_memory()
        with open(memory['config file'], 'w') as f:
            f.write(json.dumps(memory['dict'], indent=2, sort_keys=True))

    def __get_members_from_string(self, message, user_name):
        # Use mentions instead of looking up the name if possible
        if len(message.mentions) > 0:
            return message.mentions

        user_name = user_name.strip('@').split('#')[0]
        members = list()
        for member in self.client.get_all_members():
            if member.nick == user_name or member.name == user_name:
                members.append(member)
        if len(members) == 0:
            return 'Error: No member found with the name "{}"'.format(user_name)
        if len(members) > 1:
            return 'Error: Multiple members share the name "{}". Try again by mentioning the user.'.format(user_name)
        return members
