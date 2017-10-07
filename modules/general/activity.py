import glados
import re
import time
import types
import pylab as plt
import json
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


def create_author():
    author = dict()
    author['participation_per_day'] = dict()
    author['participation_per_channel'] = dict()
    author['average_day_cycle'] = [0] * 24
    author['weekly_day_cycle'] = [0] * 24
    author['recent_day_cycle'] = [0] * 24
    return author


class Activity(glados.Module):
    def setup_memory(self):
        self.memory['log_dir'] = path.join(self.local_data_dir, 'log')
        self.memory['cache dir'] = path.join(self.local_data_dir, 'activity')
        self.memory['cache file'] = path.join(self.memory['cache dir'], 'activity_cache.json')
        self.memory['cache'] = None

        if not path.exists(self.memory['cache dir']):
            makedirs(self.memory['cache dir'])

        if path.isfile(self.memory['cache file']):
            self.memory['cache'] = json.loads(open(self.memory['cache file']).read())

    def __cache_is_stale(self):
        date = datetime.now().strftime('%Y-%m-%d')
        if self.memory['cache'] is None or not self.memory['cache']['date'] == date:
            return True
        return False

    async def __reprocess_cache(self):
        # Get list of all channel log files
        files = [join(self.memory['log_dir'], f) for f in listdir(self.memory['log_dir']) if isfile(join(self.memory['log_dir'], f))]
        self.memory['cache'] = dict()
        self.memory['cache']['date'] = datetime.now().strftime('%Y-%m-%d')
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
                        if m.author not in authors:
                            authors[m.author] = create_author()
                            authors[m.author]['weekly_day_cycle'] = dict()  # gets turned into a list as a post-processing step
                            authors[m.author]['recent_day_cycle'] = dict()  # gets turned into a list as a post-processing step
                        a = authors[m.author]

                        if not log_stamp in a['participation_per_day']:
                            a['participation_per_day'][log_stamp] = 0
                        a['participation_per_day'][log_stamp] += 1

                        if not m.channel in a['participation_per_channel']:
                            a['participation_per_channel'][m.channel] = 0
                        a['participation_per_channel'][m.channel] += 1

                        a['average_day_cycle'][int(m.stamp.tm_hour)] += 1

                        if not log_stamp in a['recent_day_cycle']:
                            a['recent_day_cycle'][log_stamp] = [0] * 24
                            a['weekly_day_cycle'][log_stamp] = [0] * 24
                        a['recent_day_cycle'][log_stamp][int(m.stamp.tm_hour)] += 1
                        a['weekly_day_cycle'][log_stamp][int(m.stamp.tm_hour)] += 1

                # This process does take some time
                @types.coroutine
                def switch():
                    yield
                await switch()

        # Normalise the 24h per day statistic over the number of days the author has made messages
        for author_name, author in authors.items():
            for hour, message_count in enumerate(author['average_day_cycle']):
                author['average_day_cycle'][hour] = message_count / len(author['participation_per_day'])

        # Now that we know the last date, eliminate all but the most recent full day
        for author_name, author in authors.items():
            # stats for the last day
            day_stamps, hours = zip(*sorted(author['recent_day_cycle'].items(), key=lambda dv: dv[0]))
            author['recent_day_cycle'] = hours[-min(2, len(hours))]  # second last item
            # stats for the last week
            day_stamps, hours = zip(*sorted(author['weekly_day_cycle'].items(), key=lambda dv: dv[0]))
            author['weekly_day_cycle'] = hours[-8:len(hours)-1]  # last 8 items, omit the most recent day to make it 7
            # Accumulate and Normalise weekly statistic
            num_days_in_week = len(author['weekly_day_cycle'])
            author['weekly_day_cycle'] = [sum(msgs_at_hour) for msgs_at_hour in zip(*author['weekly_day_cycle'])]
            for hour, message_count in enumerate(author['weekly_day_cycle']):
                author['weekly_day_cycle'][hour] = message_count / num_days_in_week

        # Create a fake author that reflects the statistics of the server
        server_stats = create_author()
        for author_name, author in authors.items():
            for stamp, message_count in author['participation_per_day'].items():
                if not stamp in server_stats['participation_per_day']:
                    server_stats['participation_per_day'][stamp] = 0
                server_stats['participation_per_day'][stamp] += message_count

            for channel_name, message_count in author['participation_per_channel'].items():
                if not channel_name in server_stats['participation_per_channel']:
                    server_stats['participation_per_channel'][channel_name] = 0
                server_stats['participation_per_channel'][channel_name] += message_count

            for hour, message_count in enumerate(author['average_day_cycle']):
                server_stats['average_day_cycle'][hour] += message_count

            for hour, message_count in enumerate(author['weekly_day_cycle']):
                server_stats['weekly_day_cycle'][hour] += message_count

            for hour, message_count in enumerate(author['recent_day_cycle']):
                server_stats['recent_day_cycle'][hour] += message_count

        self.memory['cache']['authors'] = authors
        self.memory['cache']['server'] = server_stats
        with open(self.memory['cache file'], 'w') as f:
            f.write(json.dumps(self.memory['cache']))

    @glados.Module.command('ranks', '', 'Top users who post the most shit')
    async def ranks(self, message, users):
        if self.__cache_is_stale():
            await self.client.send_message(message.channel, 'Data is being reprocessed, stand by...')
            self.__reprocess_cache()

        authors = self.memory['cache']['authors']
        authors_total = dict()
        for author_name, author in authors.items():
            authors_total[author_name] = sum(v for k, v in author['participation_per_day'].items())

        top5 = list(zip(*sorted(authors_total.items(), key=lambda dv: dv[1], reverse=True)[:5]))[0]
        fmt = '. {}\n'.join(str(x+1) for x in range(5)) + '. {}'
        msg = fmt.format(*top5)
        await self.client.send_message(message.channel, msg)

    @glados.Module.command('activity', '[user]',
                           'Plots activity statistics for a user, or total server activity if no user was specified.')
    async def plot_activity(self, message, users):
        # Mentions have precedence
        if len(message.mentions) > 0:
            user_name = message.mentions[0].name
        else:
            user_name = users.split(' ', 1)[0].strip('@').split('#')[0]

        if self.__cache_is_stale():
            await self.client.send_message(message.channel, 'Data is being reprocessed, stand by...')
            await self.__reprocess_cache()

        if user_name == '':
            user = self.memory['cache']['server']
            user_name = 'Server'
        else:
            authors = self.memory['cache']['authors']
            if not user_name in authors:
                await self.client.send_message(message.channel, 'Unknown user "{}". Try mentioning him?'.format(user_name))
                return
            user = authors[user_name]

        image_file_name = self.__generate_figure(user, user_name)
        await self.client.send_file(message.channel, image_file_name)

    def __generate_figure(self, user, user_name):
        # Set up figure
        fig = plt.figure(figsize=(8, 6), dpi=150)
        fig.suptitle('{}\'s activity'.format(user_name), fontsize=20)
        ax1 = fig.add_subplot(221)
        ax2 = fig.add_subplot(222)
        ax3 = fig.add_subplot(212)

        # Plot 24 hour participation data, accumulated over all time
        t = [x for x in range(24)]
        y = [user['average_day_cycle'][x] for x in t]
        ax1.plot(t, y)
        y = [user['recent_day_cycle'][x] for x in t]
        ax1.plot(t, y)
        y = [user['weekly_day_cycle'][x] for x in t]
        ax1.plot(t, y)
        ax1.set_xlim([0, 24])
        ax1.grid()
        ax1.set_title('Daily Activity')
        ax1.set_xlabel('Hour (UTC)')
        ax1.set_ylabel('Message Count per Hour')
        ax1.legend(['Average', 'Last Day', 'Last Week'])

        # Create pie chart of the most active channels
        top5 = sorted(user['participation_per_channel'], key=user['participation_per_channel'].get, reverse=True)[:5]
        labels = top5
        sizes = [user['participation_per_channel'][x] for x in top5]
        explode = [0] * len(top5)
        explode[0] = 0.1
        ax2.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True)

        # Create overall activity
        dates, values = zip(*sorted(user['participation_per_day'].items(), key=lambda dv: dv[0]))
        dates = [datetime.fromtimestamp(float(x)) for x in dates]
        dates = date2num(dates)
        if len(values) > 80:
            ax3.bar(dates, values, width=1)
        else:
            ax3.bar(dates, values)
        ax3.xaxis_date()
        ax3.set_title('Total Activity')
        ax3.set_xlim([dates[0], dates[-1]])
        ax3.set_ylabel('Message Count per Day')
        ax3.grid()
        spacing = 2
        for label in ax3.xaxis.get_ticklabels()[::spacing]:
            label.set_visible(False)

        image_file_name = path.join(self.memory['cache dir'], user_name + '.png')
        fig.savefig(image_file_name)
        return image_file_name
