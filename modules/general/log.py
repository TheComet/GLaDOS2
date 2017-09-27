import glados
import os
from datetime import datetime


class Log(glados.Module):
    def setup_memory(self):
        self.memory['log path'] = os.path.join(self.data_dir, 'log')
        if not os.path.exists(self.memory['log path']):
            os.makedirs(self.memory['log path'])

        self.memory['date'] = datetime.now().strftime('%Y-%m-%d')
        self.memory['log file'] = open(os.path.join(self.memory['log path'], 'chanlog-{}'.format(self.memory['date'])), 'a')

    def __open_new_log_if_necessary(self):
        date = datetime.now().strftime('%Y-%m-%d')
        if not self.memory['date'] == date:
            self.memory['log file'].close()
            self.memory['date'] = date
            self.memory['log file'] = open(os.path.join(self.memory['log path'], 'chanlog-{}'.format(self.memory['date'])), 'a')

    @glados.Permissions.spamalot
    @glados.Module.rule('^.*$')
    async def on_message(self, message, match):
        server_name = message.server.name if message.server else ''
        self.__open_new_log_if_necessary()
        info = '[{0}] {1}: #{2}: {3}: {4}\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                    server_name,
                                                    message.channel.name,
                                                    message.author.name,
                                                    message.clean_content)

        self.memory['log file'].write(info)
        self.memory['log file'].flush()
        return tuple()
