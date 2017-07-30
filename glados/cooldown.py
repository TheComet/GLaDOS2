from datetime import datetime


class Tracker(object):
    """
    Helper mechanism to regulate frequent uses.  Calling `update` advances `margin` and `margin_factor`, which both
    decay over time, as determined by `margin_rate` and `punish_rate`.  Each usage increases `margin_factor` and
    consequently causes `margin` to increase exponentially.

    Properties:

        stamp          Timestamp since last checked
        margin         Value from [-max_margin, max_margin]; if >= 0, on cooldown; decreases by `margin_rate` over time
        margin_factor  Margin multiplier, increases by 1 with each check, decreases by `punish_rate` over time
        last_stamp     Stamp form last update
        last_margin    Margin from last update (unused?)


    The values in this class were determined empirically.
    """

    max_margin        = 50      # seconds
    punish_margin     = 5       # seconds
    margin_rate       = 1       # -Δ(margin)/s
    punish_rate       = 1/180   # -Δ(punish)/s

    def __init__(self, **kwargs):
        if not kwargs:
            self.stamp          = datetime.now()
            self.margin         = -self.max_margin
            self.margin_factor  = 1

            # state tracking
            self.last_margin    = self.margin
            self.last_stamp     = self.stamp
            self.last_punished  = None

        else:
            # clone
            for k, v in kwargs.items():
                setattr(self, k, v)

    def update(self, now=None):
        # update time–based state
        self.last_margin   = self.margin
        self.last_stamp    = self.stamp
        self.stamp         = now or datetime.now()
        elapsed            = (self.stamp - self.last_stamp).total_seconds()

        # decrease margin and factor depending on how long since the last check
        self.margin        = max(-self.max_margin, self.margin - elapsed*self.margin_rate)
        self.margin_factor = max(1, self.margin_factor - elapsed*self.punish_rate)

        # check if cooldown is still active, before applying margin
        result = self.margin <= 0
        if not result:
            self.last_punished = self.stamp

        # increase margin and factor, clamping margin to `max_margin`
        self.margin        = min(self.max_margin, self.margin + self.margin_factor * self.punish_margin)
        self.margin_factor += 1

        return result


    def __repr__(self):
        return "Tracker({})".format(', '.join(map(
            lambda k: "{}={}".format(k, repr(getattr(self,k,None))),
            ['stamp','margin','last_punished','last_margin','margin_factor']
        )))



class Cooldown(object):
    """
    Tracks usages by users
    """

    def __init__(self):
        self.__timestamps = dict()


    def check(self, author_name):
        """
        Checks if the author is off of cooldown or not.
        :param author_name: Name of the author to check.
        :return: Returns False if the author is still on cooldown. True if not.
        """
        if not author_name in self.__timestamps:
            self.__timestamps[author_name] = Tracker()

        return self.__timestamps[author_name].update()


    def detail_for(self, author_name):
        """
        Retrieves cooldown information for a specific user.
        Assumes `self.punish` with `author_name` has already been called.

        :param author_name: Name of author to retrieve cooldown details
        :return: user’s margin, margin_factor, and punishment decrease rate
        """

        tracker = self.__timestamps[author_name]
        return tracker.margin, tracker.margin_factor, 1/Tracker.punish_rate
