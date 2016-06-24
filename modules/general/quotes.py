import glados
import codecs
import os.path
import random
import json
from datetime import datetime
import dateutil.parser


def strip_timestamp_and_name(msg):
    try:
        dateutil.parser.parse(msg[:19])
    except TypeError or ValueError:
        return msg

    return msg[19:].split(':', 1)[1].strip()


def get_timestamp(msg):
    try:
        stamp = dateutil.parser.parse(msg[:19])
    except TypeError or ValueError:
        return None

    return stamp


def get_author(msg):
    try:
        dateutil.parser.parse(msg[:19])
    except TypeError:
        return None

    return msg[19:].split(':', 1)[0]


class Quotes(glados.Module):
    def __init__(self, settings):
        super(Quotes, self).__init__(settings)

        self.quotes_data_path = os.path.join(settings['modules']['config path'], 'quotes')
        if not os.path.exists(self.quotes_data_path):
            os.makedirs(self.quotes_data_path)

        self.__seen_file = os.path.join(settings['modules']['config path'], 'quotes', 'seen_timestamps.json')
        self.__last_seen = dict()
        self.__load_seen_timestamps()

    def get_help_list(self):
        return [
            glados.Help('quote', '<user>', 'Dig up a quote the user once said in the past.'),
            glados.Help('quotestats', '<user>', 'Provide statistics on how many quotes a user has and how'
                                                ' intelligent he is'),
            glados.Help('mentions', '[num]', 'Returns all messages in which you were mentioned since you were last seen.'
                                             ' If you provide a number, it will return the last [num] messages instead.')
        ]

    def check_nickname_valid(self, author):
        """
        Returns True if the nickname is valid. Returns a string describing the error if an error occurs.
        :param author: The nickname to check
        :return: True or an error string
        """
        if author is None:
            return 'Must pass a nickname as an argument'

        if not os.path.isfile(self.quotes_file_name(author)):
            return 'I don\'t know any quotes from {}'.format(author)

        return None

    def quotes_file_name(self, author):
        return os.path.join(self.quotes_data_path, author) + '.txt'

    def __load_seen_timestamps(self):
        glados.log('loading seen timestamps for .mentions')
        if os.path.isfile(self.__seen_file):
            self.__last_seen = json.loads(open(self.__seen_file).read())

    def __save_seen_timestamps(self):
        glados.log('saving seen timestamps for .mentions')
        with open(self.__seen_file, 'w') as f:
            f.write(json.dumps(self.__last_seen))

    # matches everything except strings beginning with a ".xxx" to ignore commands
    @glados.Module.rules('^((?!\.\w+).*)$')
    def record(self, client, message, match):
        glados.log('Recording quote')

        author = message.author.name
        with codecs.open(self.quotes_file_name(author.lower()), 'a', encoding='utf-8') as f:
            f.write(datetime.now().isoformat()[:19] + "  " + message.author.name + ": " + match.group(1) + "\n")

        key = author.lower()
        self.__last_seen[key] = datetime.now().isoformat()[:19]  # don't need microseconds
        self.__save_seen_timestamps()

        return tuple()

    @glados.Module.commands('quote')
    def quote(self, client, message, content):
        if content == '':
            yield from self.provide_help('quote', client, message)
            return

        author = content.strip('@').split('#')[0]
        error = self.check_nickname_valid(author.lower())
        if not error is None:
            yield from client.send_message(message.channel, error)
            return

        quotes_file = codecs.open(self.quotes_file_name(author.lower()), 'r', encoding='utf-8')
        lines = [strip_timestamp_and_name(x) for x in quotes_file.readlines()]
        quotes_file.close()

        lines = [x for x in lines if len(x) >= 20]

        if len(lines) > 0:
            line = random.choice(lines).strip('\n')
            yield from client.send_message(message.channel, '{0} once said: "{1}"'.format(author, line))
        else:
            yield from client.send_message(message.channel,
                                           '{} hasn\'t delivered any quotes worth mentioning yet'.format(author))

    @glados.Module.commands('quotestats')
    def quotestats(self, client, message, content):
        if content == '':
            yield from self.provide_help('quotestats', client, message)
            return

        author = content.strip('@').split('#')[0]
        error = self.check_nickname_valid(author.lower())
        if not error is None:
            yield from client.send_message(message.channel, error)
            return tuple()

        quotes_file = codecs.open(self.quotes_file_name(author.lower()), 'r', encoding='utf-8')
        lines = [strip_timestamp_and_name(x) for x in quotes_file.readlines()]
        quotes_file.close()

        number_of_quotes = len(lines)
        average_quote_length = float(sum([len(quote) for quote in lines])) / float(number_of_quotes)

        words = ' '.join(lines).split(' ')
        number_of_words = len(words)
        average_word_length = float(sum([len(quote) for quote in words])) / float(number_of_words)

        response = ('I know about {0} quotes from {1}\n'
                    'The average quote length is {2:.2f} characters\n'
                    '{3} spoke {4} words with an average length of {5:.2f} characters').format(
            number_of_quotes, author,
            average_quote_length,
            author, number_of_words, average_word_length)
        yield from client.send_message(message.channel, response)

    @glados.Module.commands('mentions')
    def on_seen(self, client, message, arg):
        glados.log('Looking for mentions for author {}'.format(message.author.name))

        try:
            num = int(arg)
        except ValueError:
            num = 0

        max_num = 5
        mentions = list()
        author = message.author.name
        key = author.lower()

        quotes_file = codecs.open(self.quotes_file_name(key), 'r', encoding='utf-8')
        lines = quotes_file.readlines()
        quotes_file.close()

        if num > max_num:
            yield from client.send_message(message.channel, 'Please, don\'t be an idiot')
            return

        if num == 0:

            if key not in self.__last_seen:
                yield from client.send_message(message.channel, '{0} has never been mentioned.'.format(author))
                return

            last_seen = dateutil.parser.parse(self.__last_seen[key])
            for msg in reversed(lines):
                stamp = get_timestamp(msg)
                if stamp is None:
                    continue
                if stamp < last_seen:  # no more new messages
                    break
                if key in strip_timestamp_and_name(msg).lower():
                    mentions.append(msg)
        else:

            for msg in reversed(lines):
                if key in strip_timestamp_and_name(msg).lower():
                    mentions.append(msg)
                    num -= 1
                if num == 0:
                    break

        if len(mentions) == 0:
            yield from client.send_message(message.channel, 'No one mentioned you.')
            return

        response = list()
        for msg in mentions:
            author = get_author(msg)
            if author is None:
                author = ''
            else:
                author = '**' + author + '**: '

            response.append(author + strip_timestamp_and_name(msg))

        yield from client.send_message(message.channel, '\n'.join(response))
