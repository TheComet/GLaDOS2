import glados
import re
import time
import jsonpickle
import pylab as plt
from os import path, listdir, makedirs
from os.path import isfile, join
from datetime import datetime
from time import strptime
from matplotlib.dates import date2num
from numpy import *


class Message(object):
    def __init__(self, raw):
        match = re.match('^\[(.*?)\](.*)$', raw)
        items = match.group(2).split(':')
        self.stamp_str = match.group(1)
        self.stamp = strptime(self.stamp_str, '%Y-%m-%d %H:%M:%S')
        self.server = items[0].strip()
        self.channel = items[1].strip('#').strip()
        self.author = items[2].strip()


class Author(object):
    def __init__(self):
        self.participation_per_day = dict()
        self.channel_participation = dict()
        self.day_cycle = dict()
        for hour in range(24):
            self.day_cycle[str(hour)] = 0


class Activity(glados.Module):

    def __init__(self, settings):
        super(Activity, self).__init__(settings)

        self.__log_dir = path.join(settings['modules']['config path'], 'log')
        self.__cache_dir = path.join(settings['modules']['config path'], 'activity')
        self.__cache_file = path.join(self.__cache_dir, 'activity_cache.json')
        self.__cache = None

        if not path.exists(self.__cache_dir):
            makedirs(self.__cache_dir)

        if path.isfile(self.__cache_file):
            self.__cache = jsonpickle.decode(open(self.__cache_file).read())

    def get_help_list(self):
        return [
            glados.Help('activity', '[user]',
                        'Plots activity statistics for a user, or total server activity if no user was specified.')
        ]

    def __cache_is_stale(self):
        date = datetime.now().strftime('%Y-%m-%d')
        if self.__cache is None or not self.__cache['date'] == date:
            return True
        return False

    def __reprocess_cache(self):
        # Get list of all channel log files
        files = [join(self.__log_dir, f) for f in listdir(self.__log_dir) if isfile(join(self.__log_dir, f))]
        self.__cache = dict()
        self.__cache['date'] = datetime.now().strftime('%Y-%m-%d')
        authors = dict()

        for f in files:
            match = re.match('^.*/chanlog-([0-9]+-[0-9]+-[0-9]+)$', f)
            if match is None:
                continue
            log_stamp = time.mktime(strptime(match.group(1), '%Y-%m-%d'))

            glados.log('processing {}'.format(f))
            with open(f, 'r') as fd:
                for line in fd:
                    if len(line) > 10:
                        m = Message(line)
                        if not m.author in authors:
                            authors[m.author] = Author()
                        a = authors[m.author]

                        if not log_stamp in a.participation_per_day:
                            a.participation_per_day[log_stamp] = 0
                        a.participation_per_day[log_stamp] += 1

                        if not m.channel in a.channel_participation:
                            a.channel_participation[m.channel] = 0
                        a.channel_participation[m.channel] += 1

                        a.day_cycle[str(m.stamp.tm_hour)] += 1

        # Normalise the 24h per day statistic over the number of days the author has made messages
        for author_name, author in authors.items():
            for hour, message_count in author.day_cycle.items():
                author.day_cycle[hour] = message_count / len(author.participation_per_day)

        self.__cache['authors'] = authors
        with open(self.__cache_file, 'w') as f:
            f.write(jsonpickle.encode(self.__cache))

    @glados.Module.commands('ranks')
    def ranks(self, message, users):
        if self.__cache_is_stale():
            yield from self.client.send_message(message.channel, 'Data is being reprocessed, stand by...')
            self.__reprocess_cache()

        authors = self.__cache['authors']
        authors_total = dict()
        for author_name, author in authors.items():
            authors_total[author_name] = sum(v for k, v in author.participation_per_day.items())

        top5 = zip(*sorted(authors_total.items(), key=lambda dv: dv[1], reverse=True)[:5])
        fmt = '. {}\n'.join(str(x+1) for x in range(5)) + '. {}'
        msg = fmt.format(*top5)
        yield from self.client.send_message(message.channel, msg)

    @glados.Module.commands('activity')
    def plot_activity(self, message, users):

        # Mentions have precedence
        if len(message.mentions) > 0:
            user_name = message.mentions[0].name
        else:
            if users == '':
                user_name = message.author.name
            else:
                user_name = users.split(' ', 1)[0].strip('@').split('#')[0]

        if self.__cache_is_stale():
            yield from self.client.send_message(message.channel, 'Data is being reprocessed, stand by...')
            self.__reprocess_cache()

        authors = self.__cache['authors']
        if not user_name in authors:
            yield from self.client.send_message(message.channel, 'Unknown user "{}". Try mentioning him?'.format(user_name))

        # Set up figure
        user = authors[user_name]
        fig = plt.figure(figsize=(8, 6), dpi=150)
        fig.suptitle('{}\'s activity'.format(user_name), fontsize=20)
        ax1 = fig.add_subplot(221)
        ax2 = fig.add_subplot(222)
        ax3 = fig.add_subplot(212)

        # Plot 24 hour participation data, accumulated over all time
        t = [x for x in range(24)]
        y = [user.day_cycle[str(x)] for x in t]
        ax1.plot(t, y)
        ax1.set_xlim([0, 24])
        ax1.grid()
        ax1.set_title('Average Activity')
        ax1.set_xlabel('Hour (UTC)')
        ax1.set_ylabel('Message Count per Hour')

        # Create pie chart of the most active channels
        top5 = sorted(user.channel_participation, key=user.channel_participation.get, reverse=True)[:5]
        labels = top5
        sizes = [user.channel_participation[x] for x in top5]
        explode = [0] * len(top5)
        explode[0] = 0.1
        ax2.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True)

        # Create overall activity
        dates, values = zip(*sorted(user.participation_per_day.items(), key=lambda dv: dv[0]))
        dates = [datetime.fromtimestamp(float(x)) for x in dates]
        dates = date2num(dates)
        ax3.bar(dates, values)
        ax3.xaxis_date()
        ax3.set_title('Total Activity')
        ax3.set_xlim([dates[0], dates[-1]])
        ax3.set_ylabel('Message Count per Day')
        ax3.grid()
        spacing = 2
        for label in ax3.xaxis.get_ticklabels()[::spacing]:
            label.set_visible(False)

        image_file_name = path.join(self.__cache_dir, user_name + '.png')
        fig.savefig(image_file_name)

        yield from self.client.send_file(message.channel, image_file_name)
