import glados
import re
import time
import asyncio
import pylab as plt
from os import listdir, makedirs
from os.path import isfile, join, exists
from datetime import datetime
from time import strptime
from matplotlib.dates import date2num
from matplotlib.gridspec import GridSpec
from matplotlib import ticker
from numpy import *
from collections import deque
from glados.tools.json import load_json_compressed, save_json_compressed
from lzma import LZMAFile
import requests, json


class Message(object):
    def __init__(self, raw):
        match = re.match('^\[(.*?)\](.*)$', raw)
        items = match.group(2).split(':')
        self.stamp_str = match.group(1)
        self.stamp = strptime(self.stamp_str, '%Y-%m-%d %H:%M:%S')
        self.server = items[0].strip()
        self.channel = items[1].strip('#').strip()
        match = re.match('^(.*)\((\d+)\)$', items[2].strip())  # need to further split author and ID
        self.author = match.group(1)
        self.author_id = match.group(2)
        self.message = items[3].strip()


def new_author_dict(author_name):
    author = dict()
    author['name'] = author_name
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


# matches words that are bot commands
comment_pattern = re.compile('`(.*?)`')
def get_commands_from_message(msg):
    cmd_prefix = '.'
    if msg.startswith(cmd_prefix):
        return [(msg[len(cmd_prefix):].split(' ', 1) + [''])[:2]]

    return [(x[len(cmd_prefix):].split(' ', 1) + [''])[:2] for x in comment_pattern.findall(msg) if
            x.startswith(cmd_prefix)]


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

        self.log_dir = join(self.local_data_dir, 'log')
        self.cache_dir = join(self.local_data_dir, 'activity')
        self.cache_file = join(self.cache_dir, 'activity_cache.json.xz')
        self.cache = None

        if not exists(self.cache_dir):
            makedirs(self.cache_dir)

        if isfile(self.cache_file):
            self.cache = load_json_compressed(self.cache_file)

    def __cache_is_stale(self):
        date = datetime.now().strftime('%Y-%m-%d')
        if self.cache is None or not self.cache['date'] == date:
            return True
        return False

    async def __reprocess_cache(self, progress_report_channel):
        # Get list of all channel log files
        files = [join(self.log_dir, f) for f in listdir(self.log_dir) if isfile(join(self.log_dir, f))]
        self.cache = dict()
        self.cache['date'] = datetime.now().strftime('%Y-%m-%d')
        authors = dict()
        total_days = dict()  # Keep track of how many days a user has existed for, so we can calculate averages

        # Let people know we're reprocessing
        last_month = None
        last_year = None
        progress_msg = await self.client.send_message(progress_report_channel, "Data is being reprocessed, stand by...")

        # We don't want to process the last log file, because it doesn't contain a full day's worth of info
        #                                  vvvvv
        for i, f in enumerate(sorted(files)[:-1]):
            match = re.match('^.*/chanlog-([0-9]+-[0-9]+-[0-9]+).txt.xz$', f)
            if match is None:
                continue
            print(f)
            log_stamp = strptime(match.group(1), '%Y-%m-%d')

            # Update the total days counter of all users we've seen so far
            for author in total_days:
                total_days[author] += 1

            # Update cycle counters to the current day
            for k, v in authors.items():
                v['day_cycle_acc_day'].appendleft([0]*24)
                v['day_cycle_acc_week'].appendleft([0]*24)
                v['commands_acc'].appendleft(0)

            try:
                for line in LZMAFile(f, 'r'):
                    # parse the message into its components (author, timestamps, channel, etc.)
                    m = Message(line.decode('utf-8'))

                    # create an entry in the top-level "authors" dict in the cache structure, if not already there
                    if m.author_id not in authors:
                        authors[m.author_id] = new_author_dict(m.author)
                        authors[m.author_id]['day_cycle_acc'] = [0]*24
                        authors[m.author_id]['day_cycle_acc_day'] = deque([[0]*24], maxlen=1)
                        authors[m.author_id]['day_cycle_acc_week'] = deque([[0]*24], maxlen=7)
                        authors[m.author_id]['commands_acc'] = deque([0], maxlen=7)
                        total_days[m.author_id] = 1

                    a = authors[m.author_id]

                    # keep track of the total message count
                    a['messages_total'] += 1

                    # See if message contains any commands
                    command_count = len(get_commands_from_message(m.message))
                    a['commands_total'] += command_count
                    a['commands_acc'][0] += command_count

                    # Accumulate message count cycles for later averaging
                    a['day_cycle_acc'][int(m.stamp.tm_hour)] += 1
                    a['day_cycle_acc_day'][0][int(m.stamp.tm_hour)] += 1
                    a['day_cycle_acc_week'][0][int(m.stamp.tm_hour)] += 1

                    # count messages per channel
                    a['channels'][m.channel] = a['channels'].get(m.channel, 0) + 1

                    # count how many messages the user makes for every day
                    key = time.mktime(log_stamp)
                    a['messages_per_day'][key] = a['messages_per_day'].get(key, 0) + 1
            except:
                continue

            # This process does take some time, so yield every month
            if not last_month == log_stamp.tm_mon:
                await asyncio.sleep(0)
                last_month = log_stamp.tm_mon

            # Update progress message whenever the year changes
            if not last_year == log_stamp.tm_year:
                await self.client.edit_message(progress_msg, "Data is being reprocessed, stand by ({})...".format(
                    log_stamp.tm_year))
                last_year = log_stamp.tm_year

        server_stats = new_author_dict('Server')

        def sum_lists(a, b):
            return [float(sum(x)) for x in zip(*[a, b])]
        def add_dicts(a, b):
            return {x: a.get(x, 0) + b.get(x, 0) for x in set(a).union(b)}

        for author, a in authors.items():
            # Calculate average day cycle using the accumulated cycle
            for i, v in enumerate(a['day_cycle_acc']):
                a['day_cycle_avg'][i] = float(v / total_days[author])
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
        self.cache['server'] = server_stats
        self.cache['authors'] = authors
        save_json_compressed(self.cache_file, self.cache)

        # Delete progress message
        await self.client.delete_message(progress_msg)

    @glados.Module.command('activity', '[user]',
                           'Plots activity statistics for a user')
    async def plot_activity(self, message, args):
        if args:
            members, roles, error = self.parse_members_roles(message, args)
            if error or len(members) == 0:
                return await self.client.send_message(message.channel, "Error, unknown user(s)")
            member_ids = [x.id for x in members]
        else:
            member_ids = [message.author.id]
        await self.plot_activity_for_ids(message.channel, member_ids)

    @glados.Module.command('activityserver', '', 'Plots activity statistics for the entire server')
    @glados.Module.command('serveractivity', '', 'Plots activity statistics for the entire server')
    async def plot_server_activity(self, message, args):
        await self.plot_activity_for_ids(message.channel, ['server'])

    @glados.Module.command('activityd', '[user]',
                           'Plots activity statistics for a user, or total server activity if no user was specified.')
    async def plot_activityd(self, message, args):
        if args:
            members, roles, error = self.parse_members_roles(message, args)
            if error or len(members) == 0:
                return await self.client.send_message(message.channel, "Error, unknown user(s)")
            member_ids = [x.id for x in members]
        else:
            member_ids = [message.author.id]
        await self.plot_activity_for_ids(message.channel, member_ids)

        resp = requests.post("http://discordgrapher.net/api/consumeusage", headers={"Content-type":"application/json"}, json=self.cache["authors"][member_ids[0]])
        if resp.status_code == 200:
            json_response = json.loads(resp.content)
            await self.client.send_message(message.channel, f"View realtime graph @ {json_response['url']}")
        else:
            await self.client.send_message(message.channel, 
                                           f"Error occured in request to discordgrapher @ {resp.status_code} : {resp.content}")

    async def plot_activity_for_ids(self, channel, member_ids):
        if self.__cache_is_stale():
            await self.__reprocess_cache(channel)

        for member_id in member_ids:
            image_file_name = self.__generate_figure(member_id)
            await self.client.send_file(channel, image_file_name)

    def __generate_figure(self, member_id):
        # Set up figure
        if member_id == 'server':
            member = self.cache['server']
            fig = plt.figure(figsize=(8, 8), dpi=150)
            gs = GridSpec(3, 2, height_ratios=[1, 1, 0.3])
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
            member = self.cache['authors'][member_id]
            fig = plt.figure(figsize=(8, 6), dpi=150)
            ax1 = fig.add_subplot(221)
            ax2 = fig.add_subplot(222)
            ax3 = fig.add_subplot(212)
        fig.suptitle('{}\'s activity'.format(member['name']), fontsize=20)

        # Plot 24 hour participation data, accumulated over all time
        t = [x for x in range(24)]
        y = [member['day_cycle_avg'][x] for x in t]
        ax1.plot(t, y)
        ax1_twin = ax1.twinx()
        ax1_twin.plot(t, cumsum(y), '--')
        #y = [member['day_cycle_avg_day'][x] for x in t]
        #ax1.plot(t, y)
        #ax1_twin.plot(t, cumsum(y), '--')
        y = [member['day_cycle_avg_week'][x] for x in t]
        ax1.plot(t, y)
        ax1_twin.plot(t, cumsum(y), '--')
        ax1.set_xlim([0, 24])
        ax1.grid()
        ax1.set_title('Daily Activity')
        ax1.set_xlabel('Hour (UTC)')
        ax1.set_ylabel('Message Count per Hour')
        ax1_twin.set_ylabel('Message Count over 1 Day')
        #ax1.legend(['Average', 'Last Day', 'Last Week'])
        ax1.legend(['Average', 'Last Week'])

        # Create pie chart of the most active channels
        top = sorted(member['channels'], key=member['channels'].get, reverse=True)[:5]
        if len(top) > 0:
            labels = top
            sizes = [member['channels'][x] for x in top]
            explode = [0] * len(top)
            explode[0] = 0.1
            ax2.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True)

        # Create overall activity
        dates_and_messages = list(zip(*sorted(member['messages_per_day'].items(), key=lambda dv: dv[0])))
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
            ax3_twin = ax3.twinx()
            ax3_twin.plot(dates, cumsum(values), 'g--')
            ax3_twin.set_ylabel('Message Count over all Time')
            ticks = ticker.FuncFormatter(lambda x, pos: '{0:g}k'.format(x / 1000))
            ax3_twin.yaxis.set_major_formatter(ticks)
            spacing = 2
            for label in ax3.xaxis.get_ticklabels()[::spacing]:
                label.set_visible(False)

        if member_id == 'server':
            # Determine loudest users, if we are server
            top = sorted(self.cache['authors'].items(), key=lambda kv: kv[1]['messages_last_week'], reverse=True)
            if len(top) > 0:
                top = top[:10]
                ax4.text(0, 0.1, 'Loudest users this week')
                for i, a in enumerate(top):
                    ax4.text(0.02, i*0.2+0.3, '{}. {} ({} msgs)'.format(i+1, a[1]['name'], a[1]['messages_last_week']))

            # Determine botspam ratios
            top = sorted(self.cache['authors'].items(),
                         key=lambda kv: 0 if kv[1]['messages_last_week'] < 5  # There are people who come on and spam some bot commands, then never return
                                          else float(kv[1]['commands_last_week'])/kv[1]['messages_last_week'],
                          reverse=True)
            if len(top) > 0:
                top = top[:10]
                ax5.text(0, 0.1, 'Bot-to-message ratios this week')
                for i, a in enumerate(top):
                    if a[1]['messages_last_week'] == 0:
                        continue
                    ax5.text(0.02, i*0.2+0.3, '{}. {} ({:.2f}%)'.format(
                        i+1, a[1]['name'], 100.0 * a[1]['commands_last_week'] / a[1]['messages_last_week']))

        image_file_name = join(self.cache_dir, member['name'] + '.png')
        fig.savefig(image_file_name)
        return image_file_name
