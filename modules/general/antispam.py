import glados
import collections
import json
import discord
import dateutil.parser
from datetime import datetime, timedelta
from os.path import join, isfile

BUFFER_LEN = 5
TIME_THRESHOLD = 2  # If the average time between messages sinks below this (in seconds), the user is muted


class AntiSpam(glados.Module):
    def __init__(self):
        super(AntiSpam, self).__init__()
        self.__times = dict()

    def setup_memory(self):
        self.memory['db file'] = join(self.data_dir, 'antispam.json')
        self.memory.setdefault('db', {})
        self.__load_db()

    @glados.Permissions.spamalot
    @glados.Module.rule('^.*$')
    async def on_message(self, message, match):
        # No need to do anything if there is no mute role
        if 'role' not in self.memory['db']:
            return ()

        await self.__unmute_expired_users()

        # moderators and above cannot be muted
        if self.require_moderator(message.author):
            return ()

        # user already muted?
        if message.author.id in self.memory['db']['users']:
            return ()

        if message.author.id not in self.__times:
            self.__times[message.author.id] = collections.deque([datetime.now()], maxlen=BUFFER_LEN)
            return tuple()

        d = self.__times[message.author.id]
        d.append(datetime.now())
        if len(d) < BUFFER_LEN:
            return tuple()

        diffs = [d[i] - d[i-1] for i in range(1, len(d))]
        s = sum(x.total_seconds() for x in diffs)
        if s < TIME_THRESHOLD * BUFFER_LEN:
            try:
                await self.__mute_user(message.author)
                msg = self.memory['db']['msg']
                msg = msg.replace('{0}', message.author.mention)
                msg = msg.replace('{1}', self.memory['db']['users'][message.author.id])
                await self.client.send_message(message.channel, msg)
            except discord.Forbidden:
                await self.client.send_message(message.channel, 'I don\' have permission to mute you, but I would')

    @glados.Permissions.admin
    @glados.Module.command('muterole', '<role name|none>', 'Activates/deactivates anti-spam. When a user spams too '
                           'much, the bot will assign him the specified role. You can configure this role\'s '
                           'permissions within discord to mute any person with this role, for example.')
    async def muterole(self, message, content):
        if content == 'none':
            self.memory['db'].pop('role', None)
            self.__save_db()
            await self.client.send_message(message.channel, 'Anti-spam deactivated')
            return

        for role in self.current_server.roles:
            if role.name == content:
                db = self.memory['db']
                db.setdefault('length', 0)
                db.setdefault('users', {})
                db.setdefault('msg', '{0} You were muted for spamming until {1}')

                muted_users = [(self.current_server.get_member(uid), exp) for uid, exp in db['users'].items()]
                muted_users = list(filter(lambda x: x[0] is not None, muted_users))

                for user, exp in muted_users:
                    self.__unmute_user(user)

                db['role'] = role.id

                for user, exp in muted_users:
                    self.__mute_user(user, exp)

                await self.client.send_message(message.channel,
                    'Role "{}" set up as mute role (mute length is {} hour(s)). Re-muted existing user(s) {}'.format(
                        role.name, self.memory['db']['length'], ', '.join(x[0].name for x in muted_users)))
                break
        else:
            await self.client.send_message(message.channel, 'No role with name "{}" found'.format(content))

    @glados.Permissions.admin
    @glados.Module.command('mutelength', '<hours>', 'Configures how long the bot should wait before removing the '
                           'mute role automatically again. Specifying 0 means the role will never be removed. Default is 0')
    async def mutelength(self, message, content):
        try:
            hours = float(content)
            if hours < 0:
                raise ValueError('Invalid value')
        except ValueError as e:
            await self.client.send_message(message.channel, 'Error: {}'.format(e))
            return

        self.memory['db']['length'] = hours
        self.__save_db()
        await self.client.send_message(message.channel, 'Mute length set to {}'.format(
            'forever' if hours == 0 else '{} hours'.format(hours)
        ))

    @glados.Permissions.admin
    @glados.Module.command('mutemessage', '<msg>', 'The message to print when a user is muted. You can use python-like '
                           'syntax "{0}" to refer the user\'s name and "{1}" to refer to the date of expiry, e.g. '
                           '"Sorry {0}, you were muted until {1}"')
    async def mutemessage(self, message, content):
        self.memory['db']['msg'] = content
        self.__save_db()
        msg = content.replace('{0}', '<user>').replace('{1}', '<expiry>')
        await self.client.send_message(message.channel, 'Message changed to "{}"'.format(msg))

    @glados.Permissions.moderator
    @glados.Module.command('mute', '<user> [user...] [duration]', 'Mutes the specified user(s)')
    async def mute(self, message, content):
        if 'role' not in self.memory['db']:
            self.client.send_message(message.channel,
                'Mute role has not been set with {}muterole. Can\'t mute.'.format(self.command_prefix))
            return

        members, roles, error = self.parse_members_roles(message, content)
        if len(members) == 0:
            error = error if error else 'Couldn\'t find any users'
            await self.client.send_message(message.channel, error)
            return

        try:
            length = float(content[-1])
        except ValueError:
            length = self.memory['db']['length']

        for user in members:
            await self.__mute_user(user, length)
        await self.client.send_message(message.channel, 'User(s) {} were muted for {} hour(s)'.format(
            ' '.join(x.name for x in members), length))

    @glados.Permissions.moderator
    @glados.Module.command('unmute', '<user> [user...]', 'Unmutes the specified user(s)')
    async def unmute(self, message, content):
        if 'role' not in self.memory['db']:
            self.client.send_message(message.channel,
                'Mute role has not been set with {}muterole. Can\'t unmute.'.format(self.command_prefix))
            return

        members, roles, error = self.parse_members_roles(message, content)
        if len(members) == 0:
            error = error if error else 'Couldn\'t find any users'
            await self.client.send_message(message.channel, error)
            return

        for user in members:
            await self.__unmute_user(user)
        await self.client.send_message(message.channel, 'User(s) {} were unmuted'.format(' '.join(x.name for x in members)))

    @glados.Module.command('mutelist', '', 'Displays a list of users who have been muted')
    async def mutelist(self, message, channel):
        muted_dict = self.memory['db'].get('users', None)
        if muted_dict is None:
            return ()

        muted_members = list()
        for member in self.current_server.members:

            expiry_date = muted_dict.get(member.id, None)
            if expiry_date is None:
                continue  # This member is not muted

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
            muted_members.append((member, time_to_expiry))

        if len(muted_members) > 0:
            strings = ['**Muted Users**']
            for member, time_to_expiry in muted_members:
                strings.append('  + ' + member.name + ' for ' + time_to_expiry)
        else:
            strings = ['No one is muted.']
        for msg in self.pack_into_messages(strings):
            await self.client.send_message(message.channel, msg)

    async def __mute_user(self, member, length):
        expiry = 'never' if length == 0 else (datetime.now() + timedelta(hours=length)).isoformat()
        self.memory['db']['users'][member.id] = expiry
        self.__save_db()

        role_id = self.memory['db']['role']
        roles = [role for role in self.current_server.roles if role.id == role_id]
        await self.client.add_roles(member, *roles)

    async def __unmute_user(self, member):
        role_id = self.memory['db']['role']
        roles = [role for role in self.current_server.roles if role.id == role_id]
        await self.client.remove_roles(member, *roles)

        self.memory['db']['users'].pop(member.id)
        self.__save_db()

    async def __unmute_expired_users(self):
        now = datetime.now().isoformat()
        muted_users = self.memory['db']['users']
        users_to_unmute = [id for id, expiry in muted_users.items() if not expiry == 'never' and now > expiry]

        for user_id in users_to_unmute:
            await self.__unmute_user(self.current_server.get_member(user_id))

    def __load_db(self):
        if isfile(self.memory['db file']):
            self.memory['db'] = json.loads(open(self.memory['db file']).read())

    def __save_db(self):
        with open(self.memory['db file'], 'w') as f:
            f.write(json.dumps(self.memory['db'], indent=2, sort_keys=True))
