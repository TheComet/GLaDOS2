import os
import random
import re
from lzma import LZMAFile
from glados import Module, Permissions


class Quotes(Module):
    def __init__(self, server_instance, full_name):
        super(Quotes, self).__init__(server_instance, full_name)

        self.quotes_dir = os.path.join(self.local_data_dir, "quotes2")
        if not os.path.exists(self.quotes_dir):
            os.mkdir(self.quotes_dir)

    # Intentionally don't match messages that contain newlines.
    @Permissions.spamalot
    @Module.rule('^(.*)$')
    async def record(self, message, match):
        self.__append_message(message.author, message.clean_content)
        return ()

    @Module.command('quote', '[user]', 'Dig up a quote the user (or yourself) once said in the past.')
    async def quote(self, message, args):
        target = message.author
        if args:
            members, roles, error = self.parse_members_roles(message, args, membercount=1, rolecount=0)
            if error:
                return await self.client.send_message(message.channel, error)
            target = members[0]

        quote = self.__get_random_message(target)
        await self.client.send_message(message.channel, '{0} once said: "{1}"'.format(target.name, quote))

    @Module.command('findquote', '<text> [user]', 'Dig up a quote the user once said containing the specified text.')
    async def findquote(self, message, args):
        args_parts = args.split(' ')
        if len(args_parts) == 1:
            target = message.author
            search_query = args.strip()
        else:
            members, roles, error = self.parse_members_roles(message, args_parts[-1])
            if error:
                target = message.author
                search_query = args.strip()
            else:
                search_query = ' '.join(args_parts[:-1]).strip()
                target = members.pop()

        quote = self.__get_random_message_matching(target, search_query)
        await self.client.send_message(message.channel, '{0} once said: "{1}"'.format(target.name, quote))

    def __remove_mentions(self, message):
        '''Remove any mentions from the quote and replace them with actual member names'''
        mentioned_ids = [x.strip('<@!>') for x in re.findall('<@!?[0-9]+>', message)]
        for mentioned_id in mentioned_ids:
            for member in self.server.members:
                if member.id == mentioned_id:
                    message = message.replace('<@{}>'.format(id), member.name).replace('<@!{}>'.format(id), member.name)
                    break
        return message.strip('<@!>')

    def __quotes_file_name(self, author):
        return os.path.join(self.quotes_dir, author.id + '.txt.xz')

    def __escape_message(self, message):
        return message.replace("\n", "\\n") + "\n"

    def __unescape_message(self, message):
        return message[:-1].replace("\\n", "\n")

    def __append_message(self, author, message):
        with LZMAFile(self.__quotes_file_name(author), "a") as f:
            message = self.__escape_message(message)
            f.write(message.encode('utf-8'))

    def __get_random_message(self, author):
        try:
            with LZMAFile(self.__quotes_file_name(author), "r") as f:
                lines = f.read().decode('utf-8').split("\n")
                return self.__remove_mentions(
                    self.__unescape_message(
                        random.choice(lines)))
        except:
            return "{} hasn\'t delivered any quotes worth mentioning yet".format(author)

    def __get_random_message_matching(self, author, search_query):
        try:
            with LZMAFile(self.__quotes_file_name(author), "r") as f:
                lines = f.read().decode('utf-8').split("\n")
                lines = [x for x in lines if re.search(r'\b' + search_query + r'\b', x, re.IGNORECASE)]
                return self.__remove_mentions(
                    self.__unescape_message(
                        random.choice(lines))).replace(search_query, '**{}**'.format(search_query))
        except:
            return "No quotes found matching \"{}\"".format(search_query)
