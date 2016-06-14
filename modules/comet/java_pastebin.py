from willie import module
from willie import web
import re

@module.rule(".*(http://pastebin.com/).*")
def java_pastebin(bot, trigger):
	text = trigger.group(1)
	if text:
		pb_id = trigger.raw.split("pastebin.com/")[1].split(" ")[0]
		page = web.get("http://pastebin.com/%s" % (pb_id))
		re_mark = re.compile('syntax: <a href="/archive/(.*)">.*</a>')
		results = re_mark.findall(page)
		if not results:
			return
		if results[0] == "java":
			bot.say("OMG that's a Java code, my eyes!")
