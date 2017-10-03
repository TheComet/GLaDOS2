import dateutil
import json
import asyncio
from datetime import datetime, timezone
from os.path import join, isfile
from glados import Module, Permissions


class Announcements(Module):
    def __init__(self, bot, full_name):
        super(Announcements, self).__init__(bot, full_name)
        self.__running_tasks = dict()

    def setup_memory(self):
        self.memory['db file'] = join(self.data_dir, 'announcements.json')
        self.memory.setdefault('db', {})
        self.__load_db()

        for ID, announcement in self.memory['db'].items():
            self.__start_announce_task(ID, announcement)

    def __start_announce_task(self, ID, announcement):
        channel_id = announcement['channel']
        message = announcement['message']
        try:
            date_or_interval = dateutil.parse(announcement['date'])
        except KeyError:
            date_or_interval = announcement['interval']

        self.__running_tasks[ID] = (asyncio.ensure_future(self.announce_task(ID,
                                                                             self.client,
                                                                             self.client.get_channel(channel_id),
                                                                             date_or_interval, message)))

    async def announce_task(self, ID, client, channel, date_or_interval, message):
        if isinstance(date_or_interval, float):
            while True:
                await asyncio.sleep(date_or_interval * 3600)
                await client.send_message(channel, message)
        else:
            delta = date_or_interval - datetime.now(timezone.utc)
            await asyncio.sleep(delta.total_seconds())
            await client.send_message(channel, message)
            self.__running_tasks.pop(ID)

    @Permissions.admin
    @Module.command('addannouncement', '<hours|date> <message>', 'Causes <message> to be sent either every <hours> '
                    'number of hours, or once at <date>. The date format is ISO 8601 (YYYY-MM-DDThh:mm:ss). For '
                    'example, the 23rd of Sep 2011 at 2am would be: 2011-09-23T02:00:00')
    async def addannouncement(self, message, content):
        date_or_hours, msg = self.__parse_date_or_hours_and_message(content)
        if date_or_hours is None:
            return await self.client.send_message(message.channel, 'Failed to parse date/hours parameter.')

        ID = self.__add_announcement(message.channel, date_or_hours, msg)
        self.__start_announce_task(ID, self.memory['db'][ID])
        await self.client.send_message(message.channel, 'Added announcement #{}'.format(ID))

    @Permissions.admin
    @Module.command('rmannouncement', '<ID>', 'Removes the specified announcement. You can get the ID with lsannouncements')
    async def rmannouncement(self, message, content):
        msg = self.__rm_announcement(content)
        msg = msg if msg else 'Successfully removed announcement #{}'.format(content)
        return await self.client.send_message(message.channel, msg)

    @Permissions.admin
    @Module.command('lsannouncements', '', 'Lists all active announcements and their IDs.')
    async def lsannouncements(self, message, content):
        pass

    @Permissions.admin
    @Module.command('modifyannouncement', '<ID> <hours|date|message>', 'Change either the interval, the date, or the '
                    'message of an announcement')
    async def modifyannouncement(self, message, content):
        parts = content.split(' ', 1)
        ID = parts[0]

        try:
            announcement_dict = self.memory['db'][ID]
        except KeyError:
            return await self.client.send_message(message.channel, 'Announcement with ID #{} not found.'.format(ID))

        date_or_hours, msg = self.__parse_date_or_hours_and_message(parts[1])
        if date_or_hours is None:
            date_or_hours = announcement_dict.get('date', None) or announcement_dict.get('interval', None)
            msg = parts[1]
            if date_or_hours is None:
                msg = announcement_dict.get('message', '(No message data)')
                self.__rm_announcement(ID)
                return await self.client.send_message(message.channel, 'This announcement appears to be corrupted. I '
                                                                       'deleted it for you. The message was: ```{}``` '
                                                                       'in case you want to add it again.'.format(msg))
        else:
            msg = announcement_dict.get('message', '(No message data)')

        self.__modify_announcement(ID, date_or_hours, msg)
        await self.client.send_message(message.channel, 'Announcement #{} was modified'.format(ID))

    @staticmethod
    def __parse_date_or_hours_and_message(content):
        """
        Extracts the date or interval from a user message.
        :param content: Received message.
        :return: Returns either the date in ISO 8061 format, or the interval as a float, or if that fails, returns None.
        """
        parts = content.split()
        for i in range(len(parts)):
            try:
                return dateutil.parse(' '.join(parts[:i+1])).isoformat(), ' '.join(parts[i:])
            except (ValueError, OverflowError):
                continue

        # well that failed, maybe it's hours
        try:
            return float(parts[0]), ' '.join(parts[1:])
        except ValueError:
            pass

        return None, None

    def __add_announcement(self, channel, interval_or_date, msg):
        typ = 'interval' if isinstance(interval_or_date, float) else 'date'
        announcement_dict = self.memory['db']
        # Find an unused ID in the dict
        ID = 1
        while ID in announcement_dict:
            ID += 1

        announcement_dict[ID] = {
            typ: interval_or_date,
            'message': msg,
            'channel': channel.id
        }
        self.__save_db()
        return ID

    def __modify_announcement(self, ID, interval_or_date, msg):
        typ = 'interval' if isinstance(interval_or_date, float) else 'date'
        try:
            channel = self.memory['db'][ID]['channel']
            self.memory['db'][ID] = {
                typ: interval_or_date,
                'message': msg,
                'channel': channel
            }
            self.__save_db()
        except KeyError:
            return 'Announcement with ID #{} not found.'.format(ID)
        return ''

    def __rm_announcement(self, ID):
        try:
            self.memory['db'].pop(ID)
            self.__save_db()
        except KeyError:
            return 'Announcement with ID #{} not found.'.format(ID)
        return ''

    def __load_db(self):
        if isfile(self.memory['db file']):
            self.memory['db'] = json.loads(open(self.memory['db file']).read())

    def __save_db(self):
        with open(self.memory['db file'], 'w') as f:
            f.write(json.dumps(self.memory['db'], indent=2, sort_keys=True))
