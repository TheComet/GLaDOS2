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

    def get_help_list(self):
        return [
            glados.Help('quote', '<user>', 'Dig up a quote the user once said in the past.'),
            glados.Help('quotestats', '<user>', 'Provide statistics on how many quotes a user has and how'
                                                ' intelligent he is')
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



    # matches everything except strings beginning with a ".xxx" to ignore commands
    @glados.Module.rules('^((?!\.\w+).*)$')
    def record(self, message, match):
        glados.log('Recording quote')

        author = message.author.name
        with codecs.open(self.quotes_file_name(author.lower()), 'a', encoding='utf-8') as f:
            f.write(match.group(1) + "\n")

        return tuple()

    @glados.Module.commands('quote')
    def quote(self, message, content):
        if content == '':
            content = message.author.name

        author = content.strip('@').split('#')[0]
        error = self.check_nickname_valid(author.lower())
        if not error is None:
            yield from self.client.send_message(message.channel, error)
            return

        quotes_file = codecs.open(self.quotes_file_name(author.lower()), 'r', encoding='utf-8')
        lines = quotes_file.readlines()
        quotes_file.close()

        lines = [x for x in lines if len(x) >= 20]

        if len(lines) > 0:
            line = random.choice(lines).strip('\n')
            yield from self.client.send_message(message.channel, '{0} once said: "{1}"'.format(author, line))
        else:
            yield from self.client.send_message(message.channel,
                                           '{} hasn\'t delivered any quotes worth mentioning yet'.format(author))

    @glados.Module.commands('quotestats')
    def quotestats(self, message, content):
        if content == '':
            content = message.author.name

        author = content.strip('@').split('#')[0]
        error = self.check_nickname_valid(author.lower())
        if not error is None:
            yield from self.client.send_message(message.channel, error)
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

        # lololol
        if author == 'newt':
            response = ('I know about {0} quotes from {1}\nAll of them are trash.'.format(number_of_quotes, author))
        yield from self.client.send_message(message.channel, response)
