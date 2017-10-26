import glados
import os
from datetime import datetime


class Log(glados.Module):
    def __init__(self, server_instance, full_name):
        super(Log, self).__init__(server_instance, full_name)

        self.log_path = os.path.join(self.local_data_dir, 'log')
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)

        self.date = datetime.now().strftime('%Y-%m-%d')
        self.log_file = open(os.path.join(self.log_path, 'chanlog-{}'.format(self.date)), 'a')

    def __open_new_log_if_necessary(self):
        date = datetime.now().strftime('%Y-%m-%d')
        if not self.date == date:
            self.log_file.close()
            self.date = date
            self.log_file = open(os.path.join(self.log_path, 'chanlog-{}'.format(self.date)), 'a')

    @glados.Permissions.spamalot
    @glados.Module.rule('^.*$', ignorecommands=False)
    async def on_message(self, message, match):
        server_name = message.server.name if message.server else ''
        self.__open_new_log_if_necessary()
        info = '[{0}] {1}: #{2}: {3}: {4}\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                    server_name,
                                                    message.channel.name,
                                                    message.author.name,
                                                    message.clean_content)

        self.log_file.write(info)
        self.log_file.flush()
        return ()
