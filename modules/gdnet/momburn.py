import glados

BURN_EMOJI = ""


class MomBurn(glados.Module):
    @glados.Permissions.spamalot
    @glados.Module.rule("^.*$")
    async def on_message(self, message, match):
        try:
            await self.client.add_reaction(message, BURN_EMOJI)
        except:
            pass

