from datetime import datetime


class Cooldown(object):

    def __init__(self, cmds_per_hour):
        self.cmds_per_hour = cmds_per_hour
        self.__timestamps = dict()

    def check(self, author_name):
        if not author_name in self.__timestamps:
            self.__timestamps[author_name] = [datetime.now()]
            return True

        self.__remove_old_timestamps(author_name)
        self.__timestamps[author_name].append(datetime.now())

        if len(self.__timestamps[author_name]) > self.cmds_per_hour:
            return False
        return True

    def __remove_old_timestamps(self, author_name):
        """
        Removes any timestamps associated with the author that are older than an hour.
        :return:
        """
        self.__timestamps[author_name] = [x for x in self.__timestamps[author_name]
                                          if not self.__older_than_an_hour(x)]

    @staticmethod
    def __older_than_an_hour(timestamp):
        delta = datetime.now() - timestamp
        hours, rem = divmod(delta.seconds, 3600)
        if hours > 0:
            return True
        else:
            return False