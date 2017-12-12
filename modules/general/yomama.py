import json
from glados import Module, Permissions
from os.path import join, dirname, realpath, isfile
from random import choice
from itertools import islice

DB_FILE = join(dirname(realpath(__file__)), 'yomama.db')


class YoMama(Module):
    def __init__(self, inst, name):
        super(YoMama, self).__init__(inst, name)
        data = self.__load_data()
        self.__enable_submissions = data.get('allow submissions', True)

    @Module.command('yomama', '', 'Generate a random Yo Mama joke')
    async def yomama(self, message, content):
        with open(DB_FILE, 'r') as f:
            joke = choice(f.read().splitlines())
            await self.client.send_message(message.channel, joke)

    @Module.command('addyomama', '<joke>', 'Submit a new yomama joke for review. It might get added!')
    async def addyomama(self, message, content):
        if not self.__enable_submissions:
            return await self.client.send_message(message.author, 'YoMama joke submissions are disabled')
        joke_id = self.add_pending(message.author.id, content)
        await self.client.send_message(message.channel, 'Your joke has been submitted for review.')
        await self.client.send_message(self.owner, 'New yomama joke was submitted! `#{} - {}`\nUse .acceptyomama to accept or .denyyomama to deny.'.format(joke_id, content))

    @Permissions.owner
    @Module.command('lsyomama', '', 'List pending yomama jokes')
    async def lsyomama(self, message, content):
        data = self.__load_data()
        jokes = ['#{} - {}'.format(joke_id, joke['joke']) for joke_id, joke in islice(data['pending'].items(), 5)]
        if len(jokes) > 0:
            for msg in self.pack_into_messages(jokes):
                await self.client.send_message(message.channel, msg)
        else:
            await self.client.send_message(message.channel, 'No pending jokes.')

    @Permissions.owner
    @Module.command('acceptyomama', '<joke id>', 'Accepts a pending joke and adds it to the DB')
    async def acceptyomama(self, message, content):
        user_id, joke = self.accept_pending(content)
        if user_id is None:
            return await self.client.send_message(message.channel, 'Unknown joke ID `{}`'.format(content))
        for member in self.client.get_all_members():
            if member.id == user_id:
                await self.client.send_message(member, 'Your yomama joke `{}` was accepted!'.format(joke))
                break
        await self.client.send_message(message.channel, 'Joke accepted.')

    @Permissions.owner
    @Module.command('rejectyomama', '<joke id> [reason]', 'Rejects a pending joke and removes it from the queue')
    async def rejectyomama(self, message, content):
        args = content.split(' ', 1)
        user_id, joke = self.take_pending(args[0])
        if user_id is None:
            return await self.client.send_message(message.channel, 'Unknown joke ID `{}`'.format(args[0]))
        for member in self.client.get_all_members():
            if member.id == user_id:
                msg = 'Your yomama joke `{}` was **rejected**!'.format(joke)
                if len(args) > 1:
                    msg += '\nReason: {}'.format(args[1])
                await self.client.send_message(member, msg)
                break
        await self.client.send_message(message.channel, 'Joke rejected.')

    @Permissions.owner
    @Module.command('yomamasubs', '<enable|disable>', 'Enable the ability for users to submit jokes')
    async def yomamasubs(self, message, content):
        data = self.__load_data()
        if content.split()[0] == 'enable':
            data['allow submissions'] = True
            self.__enable_submissions = True
            self.__save_data(data)
            await self.client.send_message(message.channel, 'YoMama submissions enabled')
        elif content.split()[0] == 'disable':
            data['allow submissions'] = False
            self.__enable_submissions = False
            self.__save_data(data)
            await self.client.send_message(message.channel, 'YoMama submissions disabled')
        else:
            await self.provide_help('yomamasubs')

    def add_pending(self, user_id, joke_text):
        data = self.__load_data()
        if len(data['pending']) > 0:
            joke_id = str(max(int(x) for x in data['pending']) + 1)
        else:
            joke_id = '1'
        data['pending'][joke_id] = dict(user_id=user_id, joke=joke_text)
        self.__save_data(data)
        return joke_id

    def take_pending(self, joke_id):
        data = self.__load_data()
        joke = data['pending'].pop(joke_id, False)
        if not joke:
            return None, None
        self.__save_data(data)
        return joke['user_id'], joke['joke']

    def accept_pending(self, joke_id):
        user_id, joke = self.take_pending(joke_id)
        if user_id is None:
            return None, None
        
        with open(DB_FILE, 'a') as f:
            f.write(joke)

        return user_id, joke

    def __load_data(self):
        file_name = join(self.global_data_dir, 'yomama.json')
        if isfile(file_name):
            return json.loads(open(file_name).read())
        return dict(pending=dict())
        
    def __save_data(self, data):
        file_name = join(self.global_data_dir, 'yomama.json')
        with open(file_name, 'w') as f:
            f.write(json.dumps(data))

