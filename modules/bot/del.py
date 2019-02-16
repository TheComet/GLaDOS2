import glados
import asyncio


DELETE_EMOJI = "\N{CROSS MARK}"


class Del(glados.Module):
    def __init__(self, server_instance, full_name):
        super(Del, self).__init__(server_instance, full_name)
        asyncio.ensure_future(self.reaction_listener_task())

    @glados.Module.bot_rule("^.*$")
    async def on_message(self, message, match):
        if not message.author == self.client.user:
            return ()
        try:
            await self.client.add_reaction(message, DELETE_EMOJI)
        except:
            pass

    async def reaction_listener_task(self):
        reaction_list = (DELETE_EMOJI,)
        def check(reaction ,user):
            if user == self.client.user:
                return False
            if not reaction.message.author == self.client.user:
                return False
            return reaction.emoji in reaction_list
        while True:
            # wait_for_reaction seems to report the reaction twice. The second time, delete_message fails because
            # the message doesn't exist. try/catch it so it doesn't shit the bed.
            try:
                result = await self.client.wait_for_reaction(check=check)
                if result.reaction.emoji == DELETE_EMOJI:
                    await self.client.delete_message(result.reaction.message)
            except:
                pass

    @glados.Module.command('del', '', 'Deletes the most recent bot message')
    async def del_most_recent(self, message, content):
        try:
            for msg in reversed(self.client.messages):
                if msg.author.id == self.client.user.id:
                    await self.client.delete_message(msg)
                    break
            await self.client.delete_message(message)
        except:
            pass
