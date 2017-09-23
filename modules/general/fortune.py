import glados
import subprocess


class Fortune(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('fortune', '', 'Generate a fortune to start off your day.')
        ]

    @glados.Module.commands('fortune')
    def fortune(self, message, content):
        fortune = subprocess.check_output(['/usr/games/fortune', '-a'])
        await self.client.send_message(message.channel, '\n'.join(fortune.decode('UTF-8').split('\\n')))
