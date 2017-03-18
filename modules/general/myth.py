import glados
import os
import codecs
import re
import random


class Myth(glados.Module):

    def __init__(self, settings):
        super(Myth, self).__init__(settings)

        self.data_path = os.path.join(settings['modules']['config path'], 'myths')
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

        self.data_file = os.path.join(self.data_path, 'myths.txt')

    def get_help_list(self):
        return [
            glados.Help('myth', '', 'Returns a random myth'),
            glados.Help('addmyth', '<text>', 'Adds a myth to the mythical database'),
            glados.Help('mythstats', '', 'Displays statistics on myths')
        ]

    @glados.Module.commands('addmyth')
    def addmyth(self, message, content):
        if content == '':
            yield from self.provide_help('addmyth', message)
            return

        author = message.author.name

        if len(content) < 20:
            yield from self.client.send_message(message.channel, 'Good myths are longer')
            return ()

        count = 0
        if os.path.isfile(self.data_file):
            with codecs.open(self.data_file, 'r', encoding='utf-8') as f:
                count = len(f.readlines())

        with codecs.open(self.data_file, 'a', encoding='utf-8') as f:
            content = content.replace(':', '\\:')
            f.write('{}:{}:{}\n'.format(count + 1, content, author))

    @glados.Module.commands('myth')
    def myth(self, message, content):
        with codecs.open(self.data_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        line = random.choice(lines).strip('\n')
        mentioned_ids = [x.strip('<@!>') for x in re.findall('<@!?[0-9]+>', line)]
        for id in mentioned_ids:
            for member in self.client.get_all_members():
                if member.id == id:
                    line = line.replace('<@{}>'.format(id), member.name).replace('<@!{}>'.format(id), member.name)
                    break

        def special_split(msg):
            ret = list()
            last_i = 0
            i = 0
            l = len(msg)
            while True:
                if i == l:
                    break
                if msg[i] == ':':
                    if msg[i-1] == '\\':
                        continue
                    ret.append(msg[last_i:i])
                    last_i = i + 1
                i += 1
            if i > last_i:
                ret.append(msg[last_i:i])
            return ret

        parts = special_split(line.strip('<@!>'))
        line = '"{}" -- *Submitted by {}*'.format(parts[1], parts[2])

        yield from self.client.send_message(message.channel, line)

    @glados.Module.commands('mythstats')
    def mythstats(self, message, content):
        if os.path.isfile(self.data_file):
            with codecs.open(self.data_file, 'r', encoding='utf-8') as f:
                count = len(f.readlines())
            yield from self.client.send_message(message.channel, 'There are {} myths submitted'.format(count))
        else:
            yield from self.client.send_message(message.channel, 'No myths.')
