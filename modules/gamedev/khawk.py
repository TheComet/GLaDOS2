import glados


class Khawk(glados.Module):
    def get_help_list(self):
        return [ glados.Help('khawk', '', 'I am not allowed to speak to you. Talk to Khawk about my availability.') ]

    @glados.Module.commands('khawk')
    def khawk(self, message, args):
        await self.client.send_message(message.channel, 'I am not allowed to speak to you. Talk to Khawk about my availability.')

