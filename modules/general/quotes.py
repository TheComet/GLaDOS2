import glados
import codecs
import os.path
import random
import collections
import re
import nltk
import pylab
import numpy as np
import enchant


class Quotes(glados.Module):
    def setup_memory(self):
        memory = self.get_memory()
        memory['quotes path'] = os.path.join(self.get_config_dir(), 'quotes')
        if not os.path.exists(memory['quotes path']):
            os.makedirs(memory['quotes path'])

        memory['dictionaries'] = [
            enchant.Dict('en_US'),
            enchant.Dict('en_GB')
        ]

    def get_help_list(self):
        return [
            glados.Help('quote', '<user>', 'Dig up a quote the user once said in the past.'),
            glados.Help('quotestats', '<user>', 'Provide statistics on how many quotes a user has and how'
                                                ' intelligent he is'),
            glados.Help('findquote', '<user> <text>', 'Dig up a quote the user once said containing the specified text.'),
            glados.Help('grep', '<word> [User]', 'Find how many times a user has said a particular word. Case-insensitive'),
            glados.Help('zipf', '[user]', 'Plot a word frequency diagram of the user.')
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
        return os.path.join(self.get_memory()['quotes path'], author) + '.txt'

    # matches everything except strings beginning with a ".xxx" to ignore commands
    @glados.Module.rules('^((?!\.\w+).*)$')
    def record(self, message, match):
        # If user has opted out, don't log
        if message.author.id in self.settings['optout']:
            return ()

        author = message.author.name
        with codecs.open(self.quotes_file_name(author.lower()), 'a', encoding='utf-8') as f:
            f.write(match.group(1) + "\n")

        return tuple()

    @glados.Module.commands('quote')
    def quote(self, message, content):
        if len(message.mentions) > 0:
            author = message.mentions[0].name
        else:
            author = content.strip('@').split('#')[0] if content != '' else message.author.name
            error = self.check_nickname_valid(author.lower())
            if error is not None:
                yield from self.client.send_message(message.channel, error)
                return

        lines = self.get_quote_lines(author)

        if len(lines) == 0:
            yield from self.client.send_message(message.channel,
                                           '{} hasn\'t delivered any quotes worth mentioning yet'.format(author))
            return

        line = random.choice(lines).strip('\n')
        line = self.remove_mentions(line)

        yield from self.client.send_message(message.channel, '{0} once said: "{1}"'.format(author, line))

    @glados.Module.commands('findquote')
    def findquote(self, message, content):
        if len(message.mentions) == 1:
            author = message.mentions[0].name
            content = content.replace('@' + author, '')
        elif len(message.mentions) > 1:
            yield from self.client.send_message(message.channel,
                                            'Multiple mentions are not supported. What are you trying to do?')
            return
        else:
            author = message.author.name
        search_query = content.strip()

        lines = self.get_quote_lines(author)
        if search_query:
            lines = [x for x in lines if search_query.lower() in x.lower()]
        
        if len(lines) == 0:
            yield from self.client.send_message(message.channel,
                                            '{} hasn\'t delivered any quotes containing "{}"'.format(author, search_query))
            return

        line = random.choice(lines).strip('\n')
        line = self.remove_mentions(line)

        yield from self.client.send_message(message.channel, '{0} once said: "{1}"'.format(author, line))

    def remove_mentions(self, text):
        '''Remove any mentions from the quote and replace them with actual member names'''
        mentioned_ids = [x.strip('<@!>') for x in re.findall('<@!?[0-9]+>', text)]
        for mentioned_id in mentioned_ids:
            for member in self.client.get_all_members():
                if member.id == mentioned_id:
                    text = text.replace('<@{}>'.format(id), member.name).replace('<@!{}>'.format(id), member.name)
                    break
        return text.strip('<@!>')

    def get_quote_lines(self, author):
        quotes_file = codecs.open(self.quotes_file_name(author.lower()), 'r', encoding='utf-8')
        lines = quotes_file.readlines()
        quotes_file.close()
        return [x for x in lines if len(x) >= 20]

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

        words = [x.strip().strip('?.",;:()[]{}') for x in ' '.join(lines).split(' ')]
        words = [x for x in words if not x == '']
        number_of_words = len(words)
        average_word_length = float(sum([len(quote) for quote in words])) / float(number_of_words)

        frequencies = collections.Counter(words)
        common = "the be to of and a in that have I it for not on with he as you do at this but his by from they we say her she or an will my one all would there their what so up out if about who get which go me when make can like time no just him know take people into year your good some could them see other than then now look only come its over think also back after use two how our work first well way even new want because any these give day most us".split()
        vocab = len(self.filter_to_english_words(set(words)))
        most_common = ', '.join(['"{}" ({})'.format(w, i) for w, i in frequencies.most_common() if w not in common][:5])
        least_common = ', '.join(['"{}"'.format(w) for w, i in frequencies.most_common() if w.find('http') == -1][-5:])

        response = ('I know about {0} quotes from {1}\n'
                    'The average quote length is {2:.2f} characters\n'
                    '{3} spoke {4} words with an average length of {5:.2f} characters\n'
                    'Your most common words are {6}\nYour least common words are {7}\n'
                    'Your vocabulary is {8}\n'
                    'NOTE: Top 100 most common words were filtered out').format(
            number_of_quotes, author,
            average_quote_length,
            author, number_of_words, average_word_length,
            most_common, least_common,
            vocab)

        yield from self.client.send_message(message.channel, response)

    def filter_to_english_words(self, words_list):
        return [word for word in words_list
                    if any(d.check(word) for d in self.get_memory()['dictionaries'])
                    and (len(word) > 1 or len(word) == 1 and word in 'aAI')]

    @glados.Module.commands('grep')
    def grep(self, message, content):
        if content == '':
            yield from self.provide_help('grep', message)
            return

        content = content.split()
        word = ' '.join(content[:-1]).strip().lower()
        # assume author is last argument
        author = content[-1].strip('@').split('#')[0]
        error = self.check_nickname_valid(author.lower())
        if not error is None:
            # take author from message instead, and take whole phrase
            author = message.author.name.strip('@').split('#')[0]
            word = ' '.join(content).strip().lower()
            error = self.check_nickname_valid(author.lower())
            if not error is None:
                yield from self.client.send_message(message.channel, error)
                return

        quotes_file = codecs.open(self.quotes_file_name(author.lower()), 'r', encoding='utf-8')
        lines = quotes_file.readlines()
        quotes_file.close()
        all_words = ' '.join(lines).lower()

        # have to use finditer if it's a phrase
        if len(word.split()) > 1:
            found_count = len([m.start() for m in re.finditer(word, all_words)])
            total_count = len(all_words.split())
        else:
            found_count = 0
            total_count = 0
            for w in all_words.split():
                total_count += 1
                if re.sub(r'\W+', '', w.strip()) == re.sub(r'\W+', '', word.strip()):
                    found_count += 1

        if found_count == 0:
            response = '{} has never said "{}"'.format(author, word)
        else:
            response = '{0} has said "{1}" {2} times ({3:.2f}‰ of all words)'.format(author, word, found_count, found_count * 1000.0 / total_count)
        yield from self.client.send_message(message.channel, response)

    @glados.Module.commands('zipf')
    def zipf(self, message, users):
        source_user = message.author.name
        source_user = source_user.strip('@').split('#')[0]

        target_users = [user.strip('@').split('#')[0] for user in users.split()]
        if len(users) == 0:
            target_users = [source_user]

        if users == '*':
            if message.server is not None:
                target_users = [member.name for member in message.server.members]
        target_users = [user for user in target_users if self.check_nickname_valid(user.lower()) is None]

        image_file_name = self.quotes_file_name(source_user.lower())[:-4] + '.png'
        pylab.title('Word frequencies')
        for user in target_users:
            quotes_file = codecs.open(self.quotes_file_name(user.lower()), 'r', encoding='utf-8')
            lines = quotes_file.readlines()
            quotes_file.close()

            if len(lines) < 20:
                continue

            tokenizer = nltk.tokenize.RegexpTokenizer(r'\w+')
            tokens = self.filter_to_english_words(tokenizer.tokenize(str(lines)))
            if len(tokens) < 200:
                continue
            freq = nltk.FreqDist(tokens)
            self.plot_word_frequencies(freq, user)

        pylab.legend()
        pylab.savefig(image_file_name)
        pylab.gcf().clear()

        yield from self.client.send_file(message.channel, image_file_name)

    @staticmethod
    def plot_word_frequencies(freq, user):
        samples = [item for item, _ in freq.most_common(50)]

        freqs = np.array([float(freq[sample]) for sample in samples])
        freqs /= np.max(freqs)

        ylabel = "Normalized word count"

        pylab.grid(True, color="silver")
        kwargs = dict()
        kwargs["linewidth"] = 2
        kwargs["label"] = user
        pylab.plot(freqs, **kwargs)
        pylab.xticks(range(len(samples)), [nltk.compat.text_type(s) for s in samples], rotation=90)
        pylab.xlabel("Samples")
        pylab.ylabel(ylabel)
        pylab.gca().set_yscale('log', basey=2)
