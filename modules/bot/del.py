import glados


class Del(glados.Module):
    @glados.Module.command('del', '', 'Deletes the most recent bot message')
    async def del_most_recent(self, message, content):
        for message in reversed(self.client.messages):
            if message.author.id == self.client.user.id:
                await self.client.delete_message(message)
                return
        return ()
