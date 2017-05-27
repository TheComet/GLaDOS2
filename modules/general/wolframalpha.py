import glados
import requests
import wolframalpha
import os.path
import random

NORMAL_RESULT = [
    "EUREKA!",
    "I think I've figured it out!",
    "The answer is:",
    "Here you go.",
    "I have determined the answer to be:",
    "Fascinating question, here is my answer:"
]

CANNOT_UNDERSTAND = [
    "I can't understand your query!",
    "speak english bro",
    "wot",
    "Sorry, what?",
    "Your query makes no sense.",
    "Your query is too complex, try simplifying it.",
    "Please be more specific."
]


class WolframAlpha(glados.Module):
    def __init__(self):
        super(WolframAlpha, self).__init__()
        self.__wolfram_client = None

    def setup_global(self):
        key = self.settings['wolfram alpha']['key']
        self.__wolfram_client = wolframalpha.Client(key)

    def setup_memory(self):
        memory = self.get_memory()
        memory['cache dir'] = os.path.join(self.get_config_dir(), 'wolfram')
        if not os.path.exists(memory['cache dir']):
            os.makedirs(memory['cache dir'])

    def get_help_list(self):
        return [glados.Help('wolfram', '<query>', 'Query Wolfram Alpha')]

    @staticmethod
    def __format_info(spellcheck, delimiters, reinterpret):
        if (spellcheck is None) and (delimiters is None) and (reinterpret is None):
            return random.choice(NORMAL_RESULT)

        lst = []

        if spellcheck is not None:
            lst.append(spellcheck)

        if delimiters is not None:
            lst.append(delimiters)

        if reinterpret is not None:
            lst.append(reinterpret)

        combined = ', and '.join(lst)

        return combined.capitalize() + '.'

    def __do_wa_query(self, query):
        try:
            data = self.__wolfram_client.query(query, params=(
                ('format', 'image'),
                ('reinterpret', 'true'),
                ('location', 'Antarctica')
            ))
        except:
            raise

        delimiters = None
        spellcheck = None
        reinterpret = None

        if 'warnings' in data:
            if 'delimiters' in data['warnings']:
                delimiters = 'an attempt was made to fix mismatched delimiters'

            if 'spellcheck' in data['warnings']:
                spellcheck = 'interpreting \'{0}\' as \'{1}\''.format(data['warnings']['spellcheck']['@word'],
                                                                      data['warnings']['spellcheck']['@suggestion'])

            if 'reinterpret' in data['warnings']:
                reinterpret = 'reinterpreting query as \'{0}\''.format(data['warnings']['reinterpret']['@new'])

        return data, self.__format_info(spellcheck, delimiters, reinterpret)

    @glados.Module.commands('wolfram')
    @glados.Module.commands('wa')
    def wolfram(self, message, query):
        if query == '':
            yield from self.provide_help('wolfram', message)
            return

        memory = self.get_memory()

        try:
            data, info_msg = self.__do_wa_query(query)
        except:
            yield from self.client.send_message(message.channel, 'Oh oh. Wolfram Alpha has experienced... an accident')
            return

        try:

            # if there is a "Result" pod, use that, otherwise use the first pod that's not an "Identity" scanner

            for pod in data['pod']:
                if pod['@id'] == 'Result':
                    subpod = pod['subpod'][0] if isinstance(pod['subpod'], list) else pod['subpod']
                    img = requests.get(subpod['img']['@src'], stream=True)
                    img.raw.decode_content = True

                    image_file_name = os.path.join(memory['cache dir'], message.author.name + '.gif')
                    with open(image_file_name, 'w+b') as f:
                        f.write(img.raw.read())
                    yield from self.client.send_file(message.channel, image_file_name,
                                                     content='{0}: {1}'.format(message.author.mention, info_msg))
                    return

            for pod in data['pod']:
                if pod['@scanner'] != 'Identity':
                    subpod = pod['subpod'][0] if isinstance(pod['subpod'], list) else pod['subpod']
                    img = requests.get(subpod['img']['@src'], stream=True)
                    img.raw.decode_content = True

                    image_file_name = os.path.join(memory['cache dir'], message.author.name + '.gif')
                    with open(image_file_name, 'w+b') as f:
                        f.write(img.raw.read())
                    yield from self.client.send_file(message.channel, image_file_name,
                                                     content='{0}: {1}'.format(message.author.mention, info_msg))
                    return

            yield from self.client.send_message(message.channel, "{0} {1}".format(message.author.mention, random.choice(CANNOT_UNDERSTAND)))
            return

        except AttributeError:
            yield from self.client.send_message(message.channel, "{0} {1}".format(message.author.mention, random.choice(CANNOT_UNDERSTAND)))
        except Exception as e:
            yield from self.client.send_message(message.channel, "{0} {1}".format(message.author.mention, random.choice(CANNOT_UNDERSTAND)))
        except:
            yield from self.client.send_message(message.channel, "{0} {1}".format(message.author.mention, random.choice(CANNOT_UNDERSTAND)))
