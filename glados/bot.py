import discord
import sys
import json
import asyncio
import inspect

import_paths_were_added = False


def add_import_paths(paths):
    global import_paths_were_added
    if not import_paths_were_added:
        for path in paths:
            sys.path.append(path)
        import_paths_were_added = True


class Bot(object):

    def __init__(self):
        self.settings = json.loads(open('settings.json').read())
        self.client = discord.Client()

        self.__modules = list()
        self.load_modules()

        @self.client.event
        @asyncio.coroutine
        def on_message(message):
            for m, callbacks in self.__modules:
                for callback in callbacks:
                    yield from callback(self.client, message)

        @self.client.event
        @asyncio.coroutine
        def on_ready():
            print('Running as', self.client.user.name)

    def load_modules(self):
        add_import_paths(self.settings['modules']['paths'])
        for modfullname in self.settings['modules']['names']:
            modnamespace = modfullname.split('.')
            classname = modnamespace[-1]
            modnamespace = '.'.join(modnamespace[:-1])

            try:
                m = __import__(modnamespace, fromlist=[classname])
                m = getattr(m, classname)(self.settings)
            except ImportError as e:
                continue

            callbacks = self.__get_module_message_callbacks(m)
            if len(callbacks) == 0:
                continue

            print("Loaded module {}".format(modfullname))
            self.__modules.append((m, callbacks))

    @staticmethod
    def __get_module_message_callbacks(m):
        return [member for name, member in inspect.getmembers(m, predicate=inspect.ismethod)
                if hasattr(member, "commands")]

    @asyncio.coroutine
    def main_task(self):
        yield from self.client.login(self.settings['login']['token'])
        yield from self.client.connect()

    def say(self, msg):
        yield from self.client.send_message(self)

    def run(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.main_task())
        except:
            loop.run_until_complete(self.client.logout())
            raise
        finally:
            loop.close()
