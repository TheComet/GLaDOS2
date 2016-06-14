from willie import module
import re
import os
import codecs
import operator

def configure(config):
    if config.option("Configure channel tracker", False):
        config.interactive_add("channeltracker", "channeltracker_data_path", "Path to where you'd like to store the permanent list of mentioned channels")

def setup(willie):
    global data_file
    global channels_dict
    data_file = os.path.join(willie.config.channeltracker.channeltracker_data_path, "channeltracker.txt")

    channels_dict = dict()
    if os.path.isfile(data_file):
        for line in codecs.open(data_file, 'r', encoding='utf-8'):
            channel = line.split(": ")[0]
            mentions = int(line.split(": ")[1])
            channels_dict[channel] = mentions

    # fill in missing folders
    if not os.path.isdir(os.path.dirname(data_file)):
        os.makedirs(os.path.dirname(data_file))

@module.commands("channels")
def list_channels(bot, trigger):
    global channels_dict
    bot.reply("Sending you a PM of all tracked channels")
    bot.msg(trigger.nick, 'How to interpret this data: #channelname(times mentioned)')
    msg = list()
    for channel, mentions in sorted(channels_dict.items(), key=operator.itemgetter(1), reverse=True):
        msg.append("#{0}({1})".format(channel, mentions))
    bot.msg(trigger.nick, ' '.join(msg))

@module.rule("(^.*channel.*$)|(^.*join.*$)|(^.*#.*$)")
def channel_mentioned(bot, trigger):
    global data_file
    global channels_dict

    message = trigger.group(0)

    # try to find the channel assuming the user used a hash prefix
    # regex from le mak
    channels = re.compile("#([^:, \[\]]{1,50})").findall(message)

    # if the user didn't use a hash, extract the first word after "channel"
    channels += re.compile("channel\s([^:, \[\]]{1,50})").findall(message)

    # if the user didn't use the word "channel" but indirectly implied it
    # by saying something like "join us in <channel>" extract the last word
    # and compare the distance to the word "join". If it is close enough then
    # it must be the channel
    words = message.split()
    try:
        join_index = words.index("join")
        if len(words) - join_index < 5: # allows 2 words between "join" and <channel>
            channels += [words[-1]] # assume channel name is the last word
    except ValueError:
        pass

    # give up
    if not channels:
        return

    channels = set([x.strip("#?!.,:;-_+/*") for x in channels])
    for channel in channels:
        if not channel in channels_dict:
            channels_dict[channel] = 0
        channels_dict[channel] += 1

    # write new channels to file
    with codecs.open(data_file, 'a', encoding='utf-8') as f:
        for channel, mentions in channels_dict.iteritems():
            f.write("{0}: {1}\n".format(channel, mentions))

