import glados


class GDNIsOffline(glados.Module):
    def get_help_list(self):
        return tuple()

    @glados.Module.rules(r'^\!profile.*$')
    @glados.Module.rules(r'^\!claim$')
    @glados.Module.rules(r'^\!rules$')
    @glados.Module.rules(r'^\!help$')
    def respond_if_down(self, message, match):
        print('fuck')
        Hodge_id = '109587405673091072'
        GDN_id = '188103830360162309'
        GDN_member = message.server.get_member(GDN_id)
        Hodge_member = message.server.get_member(Hodge_id)
        if GDN_member is None or isinstance(GDN_member, str):  # can be a string or none if the member is not found
            return tuple()
        print(GDN_member.status)
        if str(GDN_member.status) == 'offline':
            yield from self.client.send_message(message.channel, '{} is offline because {} didn\'t feed the hamster'.format(GDN_member.mention, Hodge_member.mention))
        return tuple()
