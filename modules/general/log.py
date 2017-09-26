import glados
import os
from datetime import datetime


class Log(glados.Module):
    def setup_memory(self):
        memory = self.get_memory()
        memory['log path'] = os.path.join(self.get_config_dir(), 'log')
        if not os.path.exists(memory['log path']):
            os.makedirs(memory['log path'])

        memory['date'] = datetime.now().strftime('%Y-%m-%d')
        memory['log file'] = open(os.path.join(memory['log path'], 'chanlog-{}'.format(memory['date'])), 'a')

    def get_help_list(self):
        return list()

    def __open_new_log_if_necessary(self):
        memory = self.get_memory()
        date = datetime.now().strftime('%Y-%m-%d')
        if not memory['date'] == date:
            memory['log file'].close()
            memory['date'] = date
            memory['log file'] = open(os.path.join(memory['log path'], 'chanlog-{}'.format(memory['date'])), 'a')

    @glados.Permissions.spamalot
    @glados.Module.rules('^.*$')
    def on_message(self, message, match):
        # If user has opted out, don't log
        if message.author.id in self.settings['optout']:
            return ()

        server_name = message.server.name if message.server else ''
        self.__open_new_log_if_necessary()
        info = '[{0}] {1}: #{2}: {3}: {4}\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                    server_name,
                                                    message.channel.name,
                                                    message.author.name,
                                                    message.clean_content)

        memory = self.get_memory()
        memory['log file'].write(info)
        memory['log file'].flush()
        return tuple()
