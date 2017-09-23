import glados
import os
import codecs


class Pattern(glados.Module):
    def __init__(self):
        super(Pattern, self).__init__()
        self.config_path = None

    def setup_global(self):
        self.config_path = os.path.join(self.settings['modules']['config path'], 'pattern')

    def get_help_list(self):
        return [
            glados.Help('pattern', '<language> <name>', 'Paste example code of a particular design pattern. Type "pattern <language> list" to get a list')
        ]

    @glados.Module.commands('pattern')
    def pattern(self, message, args):
        args = args.split()
        if len(args) < 2:
            await self.provide_help('pattern', message)
            return

        languages = self.list_directories(self.config_path)
        if not args[0] in languages:
            await self.client.send_message(message.channel, 'Unknown language "{}"'.format(args[0]))
            return

        patterns = self.list_files(os.path.join(self.config_path, args[0]))
        if args[1] == 'list':
            await self.client.send_message(message.channel,
                '**Available Patterns:**\n{}'.format('\n'.join(['  + ' + x for x in patterns])))
            return

        if not args[1] in patterns:
            await self.client.send_message(message.channel, 'Unknown pattern "{}"'.format(args[1]))
            return

        patterns_file = codecs.open(os.path.join(self.config_path, args[0], args[1]), 'r', encoding='utf-8')
        lines = patterns_file.readlines()
        patterns_file.close()

        await self.client.send_message(message.channel, '```{}\n{}```'.format(args[0], ''.join(lines)))

    @staticmethod
    def list_directories(path):
        return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

    @staticmethod
    def list_files(path):
        return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]