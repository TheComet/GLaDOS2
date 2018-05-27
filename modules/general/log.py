import glados
import os
from datetime import datetime
from lzma import LZMAFile


class Log(glados.Module):
    def __init__(self, server_instance, full_name):
        super(Log, self).__init__(server_instance, full_name)

        self.log_path = os.path.join(self.local_data_dir, 'log')
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)

        self.date = datetime.now().strftime('%Y-%m-%d')
        self.log_file = LZMAFile(os.path.join(self.log_path, 'chanlog-{}.txt.xz'.format(self.date)), 'a')

    def __open_new_log_if_necessary(self):
        date = datetime.now().strftime('%Y-%m-%d')
        if not self.date == date:
            self.log_file.close()
            self.date = date
            self.log_file = LZMAFile(os.path.join(self.log_path, 'chanlog-{}.txt.xz'.format(self.date)), 'a')

    @glados.Permissions.spamalot
    @glados.Module.rule('^.*$', ignorecommands=False)
    async def on_message(self, message, match):
        server_name = message.server.name if message.server else ''
        server_id = message.server.id if message.server else ''
        self.__open_new_log_if_necessary()
        info = u'[{0}] {1}({2}): #{3}: {4}({5}): {6}\n'.format(
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            server_name,
            server_id,
            message.channel.name,
            message.author.name,
            message.author.id,
            message.clean_content)

        self.log_file.write(info.encode('utf-8'))
        self.log_file.flush()
        return ()
