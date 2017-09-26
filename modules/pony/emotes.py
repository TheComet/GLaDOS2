import glados
import os
from os import listdir
from os.path import isfile
import json
import difflib
import threading

class emotes(glados.Module):
	
	def setup_global(self):
		self.emotes_path = 'modules/pony/emotesdb/'
		self.configdb_path = 'modules/pony/dbconfig/'
		self.emote_list = {}
		self.raw_emote_list = []
		self.is_running = True;
		thread = threading.Thread(target=self.build_emote_db, args=())
		thread.start()
		return
	
	def build_emote_db(self):
		self.emote_list = {}
		self.raw_emote_list = []
		files = [f for f in listdir(self.configdb_path) if isfile(self.configdb_path + f)]
		for f in files:
			subreddit = os.path.splitext(f)[0]
			json_file = open(self.configdb_path + f).read()
			jdata = json.loads(json_file)
			self.emote_list[subreddit] = {}
			for key, items in jdata.items():
				#check emote actually exists.
				name = key[1:]
				path = self.find_emote_path(name)
				if path:
					self.emote_list[subreddit][name] = name
					self.raw_emote_list.append(name)
		self.is_running = False;
		print("Finished building emote db.")
	
	def get_help_list(self):
		return [
			glados.Help('pony', '<emote>', 'Shows a pony with the specified emotion. '
                                           'Search https://ponymotes.net/view/ to find an emote or use ponylist command(note: not all emotes are supported)'),
			glados.Help('ponydel', '<emote>', 'Deletes the specified pony emote from the database, only a mod or admin can run this command.'),
			glados.Help('ponylist', '<subreddit>', "pm's you a list of emotes in the specefied subreddits, or sends a list of all subreddits if empty.  passing reload as a subreddit will cause the pony list to be rebuilt(only mod runnable)")
		]
		
	def spellcheck_emote_name(self, emote):
		r = difflib.get_close_matches(emote, self.raw_emote_list, 1, 0.2)
		if len(r)>0:
			return r[0]
		return ""

	@staticmethod
	def __concat_into_valid_message(list_of_strings):
		ret = list()
		temp = list()
		l = 0
		max_length = 1000

		if len(list_of_strings) == 0:
			return ret

		for s in list_of_strings:
			l  += len(s)
			if l >= max_length:
				ret.append('\n'.join(temp))
				l = 0
				temp = list()
			temp.append(s)
		ret.append('\n'.join(temp))
		return ret
	
	def find_emote_path(self, emotename):
		#we use replace to strip any symbols that'd allow file naviagation.
		path = self.emotes_path + emotename.replace('/','').replace('\\','').replace('.','')
		if isfile(path + ".png"):
			return path + ".png"
		if isfile(path + ".gif"):
			return path + ".gif"
		return ""
		
	def ModOnly(self, message):
		if message.author.id not in self.settings['moderators']['IDs'] and message.author.id not in self.settings['admins']['IDs']:
			yield from self.client.send_message(message.channel, "This command can only be ran by a mod, or admin.")
			return False
		return True
		
	
	@glados.Module.commands('pony')
	def request_pony_emote(self, message, content):
		
		if not content:
			yield from self.provide_help('pony', message)
			return
		path = self.find_emote_path(content)
		if not path:
			name = self.spellcheck_emote_name(content)
			if name:
				yield from self.client.send_message(message.channel, 'Unknown emoticon (did you mean: ' + name + "?)")
			else:
				yield from self.client.send_message(message.channel, 'Unknown emoticon.')
			return
		
		yield from self.client.send_file(message.channel, path)

	@glados.Module.commands('ponydel')
	def delete_pony_emote(self, message, content):
		if not self.ModOnly(message):
			return
		if not content:
			yield from self.provide_help('ponydel', message)
			return
		path = self.find_emote_path(content)
		
		if not path:
			name = self.spellcheck_emote_name(content)
			if name:
				yield from self.client.send_message(message.channel, 'Unknown emoticon (did you mean: ' + name + "?)")
			else:
				yield from self.client.send_message(message.channel, 'Unknown emoticon.')
			return
		os.remove(path)
		yield from self.client.send_message(message.channel, 'Deleted emote from db.')
		
	@glados.Module.commands('ponylist')
	def get_pony_list(self, message, content):
		response = []
		temp = ""
		per_line = 10
		i = 0
		if not content:
			response.append("List of available subreddits:")
			for key, items in self.emote_list.items():
				if i == 0:
					temp = key
				else:
					temp += " | "+key
				i += 1
				if i == per_line:
					response.append(temp)
					i = 0
			if i != 0:
				response.append(temp)
		else:
			if content=="reload":
				if not self.ModOnly(message):
					return
				if self.is_running:
					yield from self.client.send_message(message.channel, "Already rebuilding db.")
					return
				self.is_running = True
				
				thread = threading.Thread(target=self.build_emote_db, args=())
				thread.start()
				yield from self.client.send_message(message.channel, "rebuilding emote db.")
				return
			else:
				sub = self.emote_list.get(content)
				if not sub:
					response.append("Unknown subreddit.")
				else:
					response.append("List of emotes for " + content)
					for key, items in sub.items():
						if i == 0:
							temp = key
						else:
							temp += " | "+key
						i += 1
						if i == per_line:
							response.append(temp)
							i = 0
					if i != 0:
						response.append(temp)
		rlist = self.__concat_into_valid_message(response)
		for msg in rlist:
			yield from self.client.send_message(message.author, msg)