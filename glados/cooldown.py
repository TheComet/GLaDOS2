from datetime import datetime


class Tracker(object):
    """
    The values in this class were determined empirically.
    """

    max_margin = 50    # seconds
    punish_margin = 5  # seconds

    def __init__(self):
        self.stamp = datetime.now()
        self.margin = -self.max_margin
        self.last_margin = self.margin
        self.punishment_factor = 1
        self.last_punished = datetime.now()

    def punish(self, dont_punish=False):

        # first, decrease margin depending on how long since the last punishment
        self.last_margin = self.margin
        self.margin -= (datetime.now() - self.stamp).seconds
        if self.margin < -self.max_margin:
            self.margin = -self.max_margin
        self.stamp = datetime.now()

        # increase punishment with punishment factor
        self.margin += self.punish_margin * self.punishment_factor

        ret = self.margin <= 0

        if dont_punish:
            return ret

        # punish
        if ret:
            self.punishment_factor += 1
            self.last_punished = datetime.now()

        self.__decrease_punishment()

        return ret

    def __decrease_punishment(self):
        if (datetime.now() - self.last_punished).seconds > 30:
            self.punishment_factor = max(1, self.punishment_factor - 1)
            self.last_punished = datetime.now()


class Cooldown(object):

    def __init__(self):
        self.__timestamps = dict()

    def punish(self, author_name, dont_punish=False):
        """
        Checks if the author is off of cooldown or not.
        :param author_name: Name of the author to check.
        :return: Returns False if the author is still on cooldown. True if not.
        """
        if not author_name in self.__timestamps:
            self.__timestamps[author_name] = Tracker()
        return self.__timestamps[author_name].punish(dont_punish)

    def expires_in(self, author_name):
        return self.__timestamps[author_name].margin

    def punishment(self, author_name):
        return self.__timestamps[author_name].punishment_factor
