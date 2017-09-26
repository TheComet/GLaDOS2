import glados


class Khawk(glados.Module):
    @glados.Module.command('khawk', '', 'I am not allowed to speak to you. Talk to Khawk about my availability.')
    async def khawk(self, message, args):
        await self.client.send_message(message.channel, 'I am not allowed to speak to you. Talk to Khawk about my availability.')

