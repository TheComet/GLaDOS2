import glados
import re
import time
import asyncio
import pylab as plt
from os import path, listdir, makedirs
from os.path import isfile, join
from datetime import datetime
from time import strptime
from matplotlib.dates import date2num
from matplotlib.gridspec import GridSpec
from numpy import *
from collections import deque
from glados.tools.json import load_json, save_json


class Message(object):
    def __init__(self, raw):
        match = re.match('^\[(.*?)\](.*)$', raw)
        items = match.group(2).split(':')
        self.stamp_str = match.group(1)
        self.stamp = strptime(self.stamp_str, '%Y-%m-%d %H:%M:%S')
        self.server = items[0].strip()
        self.channel = items[1].strip('#').strip()
        self.author = items[2].strip()
        self.message = items[3].strip()


def new_author_dict():
    author = dict()
    author['messages_total'] = 0
    author['messages_last_week'] = 0
    author['day_cycle_avg'] = [0] * 24
    author['day_cycle_avg_week'] = [0] * 24
    author['day_cycle_avg_day'] = [0] * 24
    author['commands_total'] = 0
    author['commands_last_week'] = 0
    author['channels'] = dict()
    author['messages_per_day'] = dict()
    return author


# Cache structure is as follows:
# {
#   "authors": {
#     "author name1": {
#       "messages_total": xxx,         the total number of messages this author has made (including bot commands)
#       "messages_last_week": xxx,     the number of messages over the last 7 days
#       "commands_total": xxx,         the total number of messages that contained bot commands
#       "commands_last_week": xxx,     the number of messages that contained bot commands over the last 7 days
#       "day_cycle_avg": [0]*24,       each value is the number of messages in that hour averaged over all time
#       "day_cycle_avg_week": [0]*24,  each value is the number of messages in that hour averaged over the last week
#       "day_cycle_avg_day": [0]*24,   each value is the number of messages in that hour averaged over the last day
#       "channels": {
#         "#channel1": 10,             total number of messages in channel "#channel1"
#         "#channel2": 3               total number of messages in channel "#channel2"
#       },
#       "messages_per_day": {
#         "stamp 1": 6,                tracks how many messages the user made in that day, where the day is a timestamp
#         "stamp 2": 29                of the form "%Y-%m-%d". If the user made no messages, no entry exists.
#     }
#   },
#   "server": {
#     (same structure as an author's)
#   }
# }


class Activity(glados.Module):
    def __init__(self, server_instance, full_name):
        super(Activity, self).__init__(server_instance, full_name)

        self.log_dir = path.join(self.local_data_dir, 'log')
        self.cache_dir = path.join(self.local_data_dir, 'activity')
        self.cache_file = path.join(self.cache_dir, 'activity_cache.json')
        self.cache = None

        if not path.exists(self.cache_dir):
            makedirs(self.cache_dir)

        if path.isfile(self.cache_file):
            self.cache = load_json(self.cache_file)

    def __cache_is_stale(self):
        date = datetime.now().strftime('%Y-%m-%d')
        if self.cache is None or not self.cache['date'] == date:
            return True
        return False

    async def __reprocess_cache(self):
        # Get list of all channel log files
        files = [join(self.log_dir, f) for f in listdir(self.log_dir) if isfile(join(self.log_dir, f))]
        self.cache = dict()
        self.cache['date'] = datetime.now().strftime('%Y-%m-%d')
        authors = dict()
        total_days = 0

        # matches words that are bot commands
        command_regex = re.compile('\\' + self.command_prefix + r'\w+')

        for f in sorted(files):
            match = re.match('^.*/chanlog-([0-9]+-[0-9]+-[0-9]+)$', f)
            if match is None:
                continue
            print(f)
            log_stamp = time.mktime(strptime(match.group(1), '%Y-%m-%d'))
            total_days += 1

            # Update cycle counters to the current day
            for k, v in authors.items():
                v['day_cycle_acc_day'].appendleft([0]*24)
                v['day_cycle_acc_week'].appendleft([0]*24)
                v['commands_acc'].appendleft(0)

            for line in open(f, 'rb'):
                # parse the message into its components (author, timestamps, channel, etc.)
                m = Message(line.decode('utf-8'))

                # create an entry in the top-level "authors" dict in the cache structure, if not already there
                if m.author not in authors:
                    authors[m.author] = new_author_dict()
                    authors[m.author]['day_cycle_acc'] = [0]*24
                    authors[m.author]['day_cycle_acc_day'] = deque([[0]*24], maxlen=1)
                    authors[m.author]['day_cycle_acc_week'] = deque([[0]*24], maxlen=7)
                    authors[m.author]['commands_acc'] = deque([0], maxlen=7)

                a = authors[m.author]

                # keep track of the total message count
                a['messages_total'] += 1

                # See if message contains any commands
                command_count = len(command_regex.findall(m.message))
                a['commands_total'] += command_count
                a['commands_acc'][0] += command_count

                # Accumulate message count cycles for later averaging
                a['day_cycle_acc'][int(m.stamp.tm_hour)] += 1
                a['day_cycle_acc_day'][0][int(m.stamp.tm_hour)] += 1
                a['day_cycle_acc_week'][0][int(m.stamp.tm_hour)] += 1

                # count messages per channel
                a['channels'][m.channel] = a['channels'].get(m.channel, 0) + 1

                # count how many messages the user makes for every day
                a['messages_per_day'][log_stamp] = a['messages_per_day'].get(log_stamp, 0) + 1

            # This process does take some time
            await asyncio.sleep(0)

        server_stats = new_author_dict()

        def sum_lists(a, b):
            return [float(sum(x)) for x in zip(*[a, b])]
        def add_dicts(a, b):
            return {x: a.get(x, 0) + b.get(x, 0) for x in set(a).union(b)}

        for author, a in authors.items():
            # Calculate average day cycle using the accumulated cycle
            for i, v in enumerate(a['day_cycle_acc']):
                a['day_cycle_avg'][i] = float(v / total_days)
            # There are 7 lists of day cycles that need to be added up, then divided by 7
            a['day_cycle_avg_week'] = [float(sum(x)/7.0) for x in zip(*a['day_cycle_acc_week'])]
            # Days are easier, just use the first (and only) item
            a['day_cycle_avg_day'] = [float(x) for x in a['day_cycle_acc_day'][0]]
            a['messages_last_week'] = int(sum(sum(x) for x in zip(*a['day_cycle_acc_week'])))
            a['commands_last_week'] = int(sum(a['commands_acc']))

            # Accumulate all of these stats into the server stats
            server_stats['messages_total'] += a['messages_total']
            server_stats['messages_last_week'] += a['messages_last_week']
            server_stats['commands_total'] += a['commands_total']
            server_stats['day_cycle_avg'] = sum_lists(server_stats['day_cycle_avg'], a['day_cycle_avg'])
            server_stats['day_cycle_avg_week'] = sum_lists(server_stats['day_cycle_avg_week'], a['day_cycle_avg_week'])
            server_stats['day_cycle_avg_day'] = sum_lists(server_stats['day_cycle_avg_day'], a['day_cycle_avg_day'])
            server_stats['channels'] = add_dicts(server_stats['channels'], a['channels'])
            server_stats['messages_per_day'] = add_dicts(server_stats['messages_per_day'], a['messages_per_day'])

            # Delete the temporary keys before saving
            del a['day_cycle_acc']
            del a['day_cycle_acc_day']
            del a['day_cycle_acc_week']
            del a['commands_acc']

        # Finally, save cache
        self.cache['authors'] = authors
        self.cache['server'] = server_stats
        save_json(self.cache_file, self.cache)

    @glados.Module.command('ranks', '', 'Top users who post the most shit')
    async def ranks(self, message, users):
        if self.__cache_is_stale():
            await self.client.send_message(message.channel, 'Data is being reprocessed, stand by...')
            self.__reprocess_cache()

        authors = self.cache['authors']
        authors_total = dict()
        for author_name, author in authors.items():
            authors_total[author_name] = sum(v for k, v in author['messages_per_day'].items())

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
            user = self.cache['server']
            user_name = 'Server'
        else:
            authors = self.cache['authors']
            if user_name not in authors:
                await self.client.send_message(message.channel, 'Unknown user "{}". Try mentioning him?'.format(user_name))
                return
            user = authors[user_name]

        image_file_name = self.__generate_figure(user, user_name)
        await self.client.send_file(message.channel, image_file_name)

    def __generate_figure(self, user, user_name):
        # Set up figure
        if user_name == 'Server':
            fig = plt.figure(figsize=(8, 8), dpi=150)
            fig.suptitle('{}\'s activity'.format(user_name), fontsize=20)
            gs = GridSpec(3, 2, height_ratios=[1, 1, 0.5])
            ax1 = fig.add_subplot(gs[0])
            ax2 = fig.add_subplot(gs[1])
            ax3 = fig.add_subplot(gs[1, :])
            ax4 = fig.add_subplot(gs[4])
            ax5 = fig.add_subplot(gs[5])
            ax4.axis('off')
            ax4.set_ylim([1, 0])
            ax5.axis('off')
            ax5.set_ylim([1, 0])
        else:
            fig = plt.figure(figsize=(8, 6), dpi=150)
            fig.suptitle('{}\'s activity'.format(user_name), fontsize=20)
            ax1 = fig.add_subplot(221)
            ax2 = fig.add_subplot(222)
            ax3 = fig.add_subplot(212)

        # Plot 24 hour participation data, accumulated over all time
        t = [x for x in range(24)]
        y = [user['day_cycle_avg'][x] for x in t]
        ax1.plot(t, y)
        y = [user['day_cycle_avg_day'][x] for x in t]
        ax1.plot(t, y)
        y = [user['day_cycle_avg_week'][x] for x in t]
        ax1.plot(t, y)
        ax1.set_xlim([0, 24])
        ax1.grid()
        ax1.set_title('Daily Activity')
        ax1.set_xlabel('Hour (UTC)')
        ax1.set_ylabel('Message Count per Hour')
        ax1.legend(['Average', 'Last Day', 'Last Week'])

        # Create pie chart of the most active channels
        top5 = sorted(user['channels'], key=user['channels'].get, reverse=True)[:5]
        if len(top5) > 0:
            labels = top5
            sizes = [user['channels'][x] for x in top5]
            explode = [0] * len(top5)
            explode[0] = 0.1
            ax2.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True)

        # Create overall activity
        dates_and_messages = list(zip(*sorted(user['messages_per_day'].items(), key=lambda dv: dv[0])))
        if len(dates_and_messages) > 0:
            dates, values = dates_and_messages
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

        if user_name == 'Server':
            # Determine loudest users, if we are server
            top5 = sorted(self.cache['authors'].items(), key=lambda kv: kv[1]['messages_last_week'], reverse=True)
            if len(top5) > 0:
                top5 = top5[:5]
                ax4.text(0, 0.1, 'Loudest users this week')
                for i, a in enumerate(top5):
                    ax4.text(0.02, i*0.15+0.25, '{}. {} ({} msgs)'.format(i+1, a[0], a[1]['messages_last_week']))

            # Determine botspam ratios
            top5 = sorted(self.cache['authors'].items(),
                          key=lambda kv: 0 if kv[1]['messages_total'] < 20  # There are people who come on and spam some bot commands, then never return
                                         else float(kv[1]['commands_total'])/kv[1]['messages_total'],
                          reverse=True)
            if len(top5) > 0:
                top5 = top5[:5]
                ax5.text(0, 0.1, 'Bot-to-message ratios this week')
                for i, a in enumerate(top5):
                    ax5.text(0.02, i*0.15+0.25, '{}. {} ({:.2f}%)'.format(
                        i+1, a[0], 100.0 * a[1]['commands_total'] / a[1]['messages_total']))

        image_file_name = path.join(self.cache_dir, user_name + '.png')
        fig.savefig(image_file_name)
        return image_file_name
