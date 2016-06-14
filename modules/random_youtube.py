from willie import module
from willie import web
import re

@module.commands('iambored')
def random_youtube(bot, trigger):
	page = web.get("http://randomyoutube.net/watch")
	re_mark = re.compile('<a href="http://www\.youtube\.com/watch\?v=(.*)" target="_blank">.*</p>')
	results = re_mark.findall(page)
	if results:
		bot.say("www.youtube.com/watch?v=%s" % results[0])