import glados


class Gas(glados.Module):
    @glados.Module.command('gas', '', 'Gas')
    async def gas(self, message, user):
        if not user:
            await self.client.send_message(message.channel, "Ab ins gas du Jude!")
        else:
            if not user.lower().find("glados") == -1:
                await self.client.send_message(message.channel, "Nice try. Get comfortable while I warm up the neurotoxin emitters.")
            else:
                await self.client.send_message(user + ": Ab ins gas du Jude!")
