import willie.module
import codecs
import os.path
import random

def configure(config):
  if config.option('Configure quotes', False):
    config.interactive_add('quotes', 'quotes_data_path', "Path to where you'd like the user quotes to be stored (should be an absolute path to an existing directory).")

def setup(willie):
  global quotes_data_path
  quotes_data_path = willie.config.quotes.quotes_data_path

def check_nickname_valid(nickname, bot):
  if nickname is None:
    bot.reply("Must pass a nickname as an argument")
    return False

  if not os.path.isfile(quotes_file_name(nickname)):
    bot.reply("I don't know any quotes from %s" % (nickname))
    return False

  return True

def quotes_file_name(nickname):
  return os.path.join(quotes_data_path, nickname) + '.txt'

@willie.module.rule("^(.*)$")
def record(bot, trigger):
  with codecs.open(quotes_file_name(trigger.nick.lower()), 'a', encoding='utf-8') as f:
    f.write(trigger.group(1) + "\n")

@willie.module.commands('quote')
def quote(bot, trigger):
  nickname = trigger.group(3).lower()

  if not check_nickname_valid(nickname, bot):
    return

  quotes_file = codecs.open(quotes_file_name(nickname), 'r', encoding='utf-8')
  lines = quotes_file.readlines()
  quotes_file.close()

  lines = [x for x in lines if len(x) >= 20]

  if len(lines) > 0:
    line = random.choice(lines)
    bot.say("%s once said: \"%s\"" % (nickname, line))
  else:
    bot.say("%s hasn't delivered any quotes worth mentioning yet" % (nickname))

@willie.module.commands('quotestats')
def quotestats(bot, trigger):
  nickname = trigger.group(3).lower()

  if not check_nickname_valid(nickname, bot):
    return

  quotes_file = codecs.open(quotes_file_name(nickname), 'r', encoding='utf-8')
  lines = quotes_file.readlines()
  quotes_file.close()

  number_of_quotes = len(lines)
  average_quote_length = float(sum([len(quote) for quote in lines])) / float(number_of_quotes)

  words = ' '.join(lines).split(' ')
  number_of_words = len(words)
  average_word_length = float(sum([len(quote) for quote in words])) / float(number_of_words)

  bot.say("I know about %i quotes from %s" % (number_of_quotes, nickname))
  bot.say("The average quote length is %.2f characters" % (average_quote_length))
  bot.say("%s spoke %i words with an average length of %.2f characters" % (nickname, number_of_words, average_word_length))
