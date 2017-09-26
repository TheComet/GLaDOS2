import glados
import os
import codecs
import re
import random


class Myth(glados.Module):

    def setup_memory(self):
        self.memory['data path'] = os.path.join(self.data_dir, 'myths')
        if not os.path.exists(self.memory['data path']):
            os.makedirs(self.memory['data path'])
        self.memory['data file'] = os.path.join(self.memory['data path'], 'myths.txt')

    @glados.Module.command('addmyth', '<text>', 'Adds a myth to the mythical database')
    async def addmyth(self, message, content):
        if content == '':
            await self.provide_help('addmyth', message)
            return

        author = message.author.name

        if len(content) < 10:
            await self.client.send_message(message.channel, 'Good myths are longer')
            return ()

        new_id = 1
        if os.path.isfile(self.memory['data file']):
            with codecs.open(self.memory['data file'], 'r', encoding='utf-8') as f:
                lines = [x for x in f.readlines() if len(x) > 2]
                if len(lines) > 0:
                    last_line = lines[-1]
                    parts = self.__extract_parts(last_line)
                    new_id = int(parts[0]) + 1

        with codecs.open(self.memory['data file'], 'a', encoding='utf-8') as f:
            content = content.replace('\n', '\\n')
            f.write('{}:{}:{}\n'.format(new_id, content, author))

        await self.client.send_message(message.channel, 'Myth #{} added.'.format(new_id))

    @glados.Module.command('delmyth', '<ID> [ID 2] [ID 3]...', 'Delete offending myths')
    async def delmyth(self, message, content):
        if content == '':
            await self.provide_help('delmyth', message)
            return

        if not self.require_moderator(message.author):
            await self.client.send_message(message.channel, 'Only botmods can delete myths')
            return ()

        if not os.path.isfile(self.memory['data file']):
            await self.client.send_message(message.channel, 'Myth dB does not exist')
            return

        with codecs.open(self.memory['data file'], 'r', encoding='utf-8') as f:
            lines = f.readlines()
            replace_lines = list()
            if len(lines) == 0:
                await self.client.send_message(message.channel, 'All myths have been deleted')
                return ()
            for line in lines:
                parts = self.__extract_parts(line)
                if not parts[0] in content.split():
                    replace_lines.append(line)
                    continue
                offender = parts[2]
                deleter = message.author.name
                await self.client.send_message(message.channel, 'Myth #{} by {} was deleted by {}'.format(
                    parts[0], offender, deleter))

        # overwrite with filtered list of lines
        with codecs.open(self.memory['data file'], 'w', encoding='utf-8') as f:
            f.writelines(replace_lines)

    @glados.Module.command('myth', '[ID]', 'Returns a random myth. Botmods can specify an ID.')
    async def myth(self, message, content):
        with codecs.open(self.memory['data file'], 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if len(lines) == 0:
            await self.client.send_message(message.channel, 'No myths in dB')
            return

        # Extract a specific ID if you are a botmod
        if len(content) > 0:
            if not self.require_moderator(message.author):
                await self.client.send_message(message.channel, 'Only botmods can pass IDs')
                return ()

            line = ''
            for l in lines:
                parts = self.__extract_parts(l)
                if parts[0] == content.strip():
                    line = l
                    break
            if line == '':
                await self.client.send_message(message.channel, 'Myth #{} does not exist'.format(content.strip()))
                return
        else:
            line = random.choice(lines)

        parts = self.__extract_parts(line)
        line = 'Myth #{}: "{}" -- *Submitted by {}*'.format(parts[0], parts[1], parts[2])

        await self.client.send_message(message.channel, line)

    @glados.Module.command('mythstats', '', 'Displays statistics on myths')
    async def mythstats(self, message, content):
        if os.path.isfile(self.memory['data file']):
            with codecs.open(self.memory['data file'], 'r', encoding='utf-8') as f:
                lines = [x for x in f.readlines() if len(x) > 2]
                count = len(lines)
                last_id = count
                if len(lines) > 0:
                    last_line = lines[-1]
                    parts = self.__extract_parts(last_line)
                    last_id = int(parts[0])
            await self.client.send_message(message.channel, 'There are {} active myths submitted ({} were deleted)'.format(count, last_id - count))
        else:
            await self.client.send_message(message.channel, 'No myths.')

    def __extract_parts(self, line):
        mentioned_ids = [x.strip('<@!>') for x in re.findall('<@!?[0-9]+>', line)]
        for id in mentioned_ids:
            for member in self.current_server.members:
                if member.id == id:
                    line = line.replace('<@{}>'.format(id), member.name).replace('<@!{}>'.format(id), member.name)
                    break

        bad_parts = line.split(':')
        parts = [
            bad_parts[0],
            ':'.join(bad_parts[1:-1]),
            bad_parts[-1].strip()
        ]

        parts[1] = parts[1].replace('\\n', '\n')
        return parts
