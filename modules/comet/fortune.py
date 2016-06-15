import glados
import subprocess


class Fortune(glados.Module):

    @glados.Module.commands('fortune')
    def fortune(self, client, message, content):
        fortune = subprocess.check_output(['/usr/games/fortune'])
        yield from client.send_message(message.channel, '\n'.join(fortune.decode('UTF-8').split('\\n')))

    @glados.Module.commands('bofh')
    def bastard_operator_from_hell_quote(self, client, message, content):
        excuse = subprocess.check_output(['/usr/games/fortune', 'bofh-excuses'])
        yield from client.send_message(message.channel, '\n'.join(excuse.decode('UTF-8').split('\\n')))
