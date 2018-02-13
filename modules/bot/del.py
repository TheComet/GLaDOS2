import glados


class Del(glados.Module):
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
