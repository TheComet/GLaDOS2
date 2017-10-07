import dateutil.parser
import json
import asyncio
from datetime import datetime, timezone, timedelta
from os.path import join, isfile
from glados import Module, Permissions


class AnnounceInfo(object):
    def __init__(self, client, ID):
        self.client = client
        self.ID = ID
        self.message = None
        self.date = None
        self.interval = None
        self.channel = None

    def read_from_db(self, data):
        d = data.get(str(self.ID), None)
        if d is None:
            raise RuntimeError('Announcement with ID #{} not found.'.format(self.ID))

        self.date = d.get('date', None)
        self.interval = d.get('interval', None)
        self.message = d.get('message', None)
        channel_id = d.get('channel', None)

        if (self.date is None and self.interval is None) or self.message is None or channel_id is None:
            data.pop(str(self.ID))
            raise RuntimeError('This announcement appears to be corrupted.')

        self.channel = self.client.get_channel(channel_id)
        if self.channel is None:
            raise RuntimeError('Failed to get channel with ID {}'.format(channel_id))

    def parse_from_message(self, message, content):
        self.channel = message.channel

        parts = content.split()
        success = False
        for i in range(len(parts)):
            try:
                self.date = dateutil.parser.parse(' '.join(parts[:i+1]))
                self.message = ' '.join(parts[i+1:])
                success = True
            except (ValueError, OverflowError):
                pass
        if success:
            return

        # well that failed, maybe it's hours
        try:
            self.interval = float(parts[0])
            self.message = ' '.join(parts[1:])
        except ValueError:
            raise RuntimeError('Failed to parse date/interval')

    def write_to_db(self, data):
        typ = 'date' if self.date else 'interval'
        if self.is_date:
            date_or_interval = self.date.isoformat()
        else:
            date_or_interval = self.interval
        data[str(self.ID)] = {
            typ: date_or_interval,
            'message': self.message,
            'channel': self.channel.id
        }

    @property
    def is_interval(self):
        return self.interval is not None

    @property
    def is_date(self):
        return self.date is not None


class Announcements(Module):
    def __init__(self, bot, full_name):
        super(Announcements, self).__init__(bot, full_name)
        self.__running_tasks = dict()

    def setup_memory(self):
        self.memory['db file'] = join(self.local_data_dir, 'announcements.json')
        self.memory.setdefault('db', {})
        self.__load_db()

        for ID, announcement in self.memory['db'].items():
            a = self.__load_announcement(ID)
            self.__start_announce_task(a)

    def __start_announce_task(self, a):
        self.__running_tasks[a.ID] = asyncio.ensure_future(self.announce_task(a))

    async def announce_task(self, a):
        if a.is_interval:
            while True:
                await asyncio.sleep(a.interval * 3600)
                await a.client.send_message(a.channel, a.message)
        else:
            delta = a.date - datetime.now(timezone.utc)
            if delta > timedelta(hours=0):
                await asyncio.sleep(delta.total_seconds())
            await a.client.send_message(a.channel, a.message)
            self.__running_tasks.pop(a.ID)

    @Permissions.admin
    @Module.command('addannouncement', '<hours|date> <message>', 'Causes <message> to be sent either every <hours> '
                    'number of hours, or once at <date>. The date format is ISO 8601 (YYYY-MM-DDThh:mm:ss). For '
                    'example, the 23rd of Sep 2011 at 2am would be: 2011-09-23T02:00:00')
    async def addannouncement(self, message, content):
        try:
            a = self.__new_announcement(message, content)
            self.__write_announcement(a)
            self.__start_announce_task(a)
        except RuntimeError as e:
            return await self.client.send_message(message.channel, str(e))

        await self.client.send_message(message.channel, 'Added announcement #{}'.format(a.ID))

    @Permissions.admin
    @Module.command('rmannouncement', '<ID>', 'Removes the specified announcement. You can get the ID with lsannouncements')
    async def rmannouncement(self, message, content):
        if self.__rm_announcement(content):
            await self.client.send_message(message.channel, 'Removed announcement #{}'.format(content))
        else:
            await self.client.send_message(message.channel, 'No such announcement with ID #{}'.format(content))

    @Permissions.admin
    @Module.command('lsannouncements', '', 'Lists all active announcements and their IDs.')
    async def lsannouncements(self, message, content):
        strings = list()
        for ID, a_dict in self.memory['db'].items():
            try:
                a = self.__load_announcement(ID)
            except RuntimeError:
                self.__rm_announcement(ID)
            strings += ['({}) #{}: {}'.format(a.ID, a.channel.name, a.message)]

        for msg in self.pack_into_messages(strings):
            await self.client.send_message(message.channel, msg)

    @Permissions.admin
    @Module.command('modifyannouncement', '<ID> <hours|date|message>', 'Change either the interval, the date, or the '
                    'message of an announcement')
    async def modifyannouncement(self, message, content):
        pass

    def __new_announcement(self, message, content):
        announcement_dict = self.memory['db']
        ID = 1
        while str(ID) in announcement_dict:
            ID += 1
        a = AnnounceInfo(self.client, ID)
        a.parse_from_message(message, content)
        return a

    def __load_announcement(self, ID):
        a = AnnounceInfo(self.client, ID)
        a.read_from_db(self.memory['db'])
        return a

    def __write_announcement(self, a):
        a.write_to_db(self.memory['db'])
        self.__save_db()

    def __rm_announcement(self, ID):
        try:
            self.memory['db'].pop(str(ID))
            self.__save_db()
            task = self.__running_tasks.get(ID, None)
            if task:
                task.cancel()
            return True
        except KeyError:
            return False

    def __load_db(self):
        if isfile(self.memory['db file']):
            self.memory['db'] = json.loads(open(self.memory['db file']).read())

    def __save_db(self):
        with open(self.memory['db file'], 'w') as f:
            f.write(json.dumps(self.memory['db'], indent=2, sort_keys=True))
