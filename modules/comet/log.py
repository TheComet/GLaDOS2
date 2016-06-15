import glados
import os
from datetime import datetime


class Log(glados.Module):

    def __init__(self, settings):
        super(Log, self).__init__(settings)

        log_file = os.path.join(settings['modules']['config path'], 'log.txt')
        self.__log = open(log_file, 'a')

    @glados.Module.rules('^.*$')
    def on_message(self, client, message, match):
        info = '[{0}] {1}: #{2}: {3}: {4}\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                    message.server.name,
                                                    message.channel.name,
                                                    message.author.name,
                                                    message.clean_content)
        self.__log.write(info)
        self.__log.flush()
        return tuple()
