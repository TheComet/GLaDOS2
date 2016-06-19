import glados
import os


class Emotes(glados.Module):

    emotes_path = 'modules/bronydom/GLaDOS_ponyemotes'

    def __init__(self, settings):
        super().__init__(settings)

    def get_help_list(self):
        return [
            glados.Help('pony', '<emote>', 'Shows a pony with the specified emotion. '
                                           'Use ".help pony" to get a list of emotes')
        ]

    def get_emotes_list(self):
        return [f for f in os.listdir(self.emotes_path)
                if os.path.isfile(os.path.join(self.emotes_path, f))]

    @glados.Module.commands('pony')
    def request_pony_emote(self, client, message, content):

        if content == '':
            yield from self.provide_help('pony', client, message)
            return

        emotes = self.get_emotes_list()
        emote = [emote for emote in emotes if content in emote]
        if not emote or '/' in content:
            yield from client.send_message(message.channel, 'Unknown emoticon')
            return
        emote = emote[0]

        emote_file = os.path.join(self.emotes_path, emote)
        yield from client.send_file(message.channel, emote_file)

    @glados.Module.commands('help')
    def request_list_of_emotes(self, client, message, content):
        if content == '':
            return tuple()

        emotes = [f.strip('.png').strip('.gif') for f in self.get_emotes_list()]
        yield from client.send_message(message.channel, 'I am sending you a list of pony emotes!')
        yield from client.send_message(message.author,
                                       'Here is a list of emotes that can be used with `.pony <emote>`\n  {}'.format(
                                           '  \n'.join(emotes)
                                       ))