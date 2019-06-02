import glados

BURN_EMOJI = "\N{FIRE}"


class MomBurn(glados.Module):
    @glados.Module.rule(r"^.*(yo)?ur\s+(mom|mum|mother|momma|mama)\b.*$")
    async def on_message(self, message, match):
        try:
            await self.client.add_reaction(message, BURN_EMOJI)
        except:
            pass

