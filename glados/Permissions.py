from .module import Module


class Permissions(Module):

    BANNED = -1
    NEED_MODERATOR = -2
    NEED_ADMIN = -3
    NEED_OWNER = -4

    SPAMABLE = 1
    PUNISHABLE = 2

    def is_banned(self, member):
        return False

    def is_blessed(self, member):
        return False

    def is_server_authorized(self):
        return True

    def require_moderator(self, member):
        return False

    def require_admin(self, member):
        return False

    def require_owner(self, member):
        return False

    def get_ban_expiry(self, member):
        raise NotImplementedError()

    async def inform_about_failure(self, message, permission_code):
        """
        If check_permissions() doesn't return OK, then you can call this to send a direct message to the user informing
        him why it failed. The returned permission code from check_permissions() needs to be passed to this method.
        :param message: The discord message object
        :param permission_code: The permission code returned from check_permissions()
        """
        if permission_code == self.BANNED:
            expiry = self.get_ban_expiry(message.author)
            await self.client.send_message(message.author,
                    'You have been banned from using the bot. Your ban expires: {}'.format(expiry))
        elif permission_code == self.NEED_MODERATOR:
            await self.client.send_message(message.channel,
                    'You need to be a moderator to use this command.')
        elif permission_code == self.NEED_ADMIN:
            await self.client.send_message(message.channel,
                    'You need to be an admin to use this command.')
        elif permission_code == self.NEED_OWNER:
            await self.client.send_message(message.channel,
                    'You need to be the bot owner to use this command.')

    def check_permissions(self, member, callback_function):
        """
        Checks if the member has permission to get a response from the sepcified callback.
        :param member: A discord member instance
        :param callback_function: A handle to a module's callback method
        :return: True if the member has permission, False if otherwise
        """
        # Spammable functions are always allowed to be used, even if the user is banned
        if hasattr(callback_function, 'spamalot'):
            return self.SPAMABLE

        owner = self.require_owner(member)
        admin = self.require_admin(member)
        moderator = self.require_moderator(member)
        if hasattr(callback_function, 'owner') and not owner:
            return self.NEED_OWNER
        if hasattr(callback_function, 'admin') and not admin:
            return self.NEED_ADMIN
        if hasattr(callback_function, 'moderator') and not moderator:
            return self.NEED_MODERATOR

        if self.is_banned(member) and not owner:
            return self.BANNED

        # If member is blessed, or a mod or higher, then they can spam
        if self.is_blessed(member) or owner or admin or moderator:
            return self.SPAMABLE

        return self.PUNISHABLE

    @staticmethod
    def spamalot(func):
        """
        This should be used as a decorator to mark functions in your module that should *not* be affected by
        cooldown. This is for things like logging functions or other functions that don't directly interact with
        the user but need to monitor lots of chat messages.
        """
        func.__dict__['spamalot'] = True
        return func

    @staticmethod
    def owner(func):
        func.__dict__['owner'] = True
        return func

    @staticmethod
    def admin(func):
        func.__dict__['admin'] = True
        return func

    @staticmethod
    def moderator(func):
        func.__dict__['moderator'] = True
        return func
