import glados
import codecs
import os.path
import random


class Quotes(glados.Module):
    def __init__(self, settings):
        super(Quotes, self).__init__(settings)
        self.quotes_data_path = os.path.join(settings['modules']['config path'], 'quotes')
        if not os.path.exists(self.quotes_data_path):
            os.makedirs(self.quotes_data_path)

    def check_nickname_valid(self, nickname):
        """
        Returns True if the nickname is valid. Returns a string describing the error if an error occurs.
        :param nickname: The nickname to check
        :return: True or an error string
        """
        if nickname is None:
            return 'Must pass a nickname as an argument'

        if not os.path.isfile(self.quotes_file_name(nickname)):
            return 'I don\'t know any quotes from {}'.format(nickname)

        return True

    def quotes_file_name(self, nickname):
        return os.path.join(self.quotes_data_path, nickname) + '.txt'

    @glados.Module.rules('^(.*)$')
    def record(self, client, message, match):
        author = message.author.name
        with codecs.open(self.quotes_file_name(author.lower()), 'a', encoding='utf-8') as f:
            f.write(match.group(1) + "\n")
        return tuple()

    @glados.Module.commands('quote')
    def quote(self, client, message, content):
        author = content.strip('@').split('#')[0]

        if not self.check_nickname_valid(author.lower()):
            return tuple()

        quotes_file = codecs.open(self.quotes_file_name(author.lower()), 'r', encoding='utf-8')
        lines = quotes_file.readlines()
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
        author = content.strip('@').split('#')[0]

        if not self.check_nickname_valid(author.lower()):
            return tuple()

        quotes_file = codecs.open(self.quotes_file_name(author.lower()), 'r', encoding='utf-8')
        lines = quotes_file.readlines()
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