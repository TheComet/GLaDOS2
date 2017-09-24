import glados
import os
from os import listdir
from os.path import isfile, join
import json;
import difflib;

class Emotes(glados.Module):
	emotes_path = 'modules/pony/emotesdb/';
	configdb_path = 'modules/pony/dbconfig/';
	EmoteList = {};
	RawEmoteList = [];
	
	def __init__(self):
		super(Emotes, self).__init__();
		Files = [f for f in listdir(self.configdb_path) if isfile(join(self.configdb_path, f))];
		for f in Files:
			Subreddit = os.path.splitext(f)[0];
			JSON_File = open(self.configdb_path+f).read();
			JSON = json.loads(JSON_File);
			self.EmoteList[Subreddit] = {};
			for key, items in JSON.items():
				Name = key[1:].replace('/','').replace('\\','').replace('.','');
				Found = False; #Check we actually have it.
				Path = self.emotes_path+Name;
				if isfile(Path+".png"):
					Path = Path+".png";
					Found = True;
				if not Found and isfile(Path+".gif"):
					Path = Path+".gif";
					Found=True;
				if Found is True:
					self.EmoteList[Subreddit][Name] = Name;
					self.RawEmoteList.append(Name);
		return;
		
	def get_help_list(self):
		return [
			glados.Help('pony', '<emote>', 'Shows a pony with the specified emotion. '
                                           'Search https://ponymotes.net/view/ to find an emote or use ponylist command(note: not all emotes are supported)'),
			glados.Help('ponydel', '<emote>', 'Deletes the specified pony emote from the database, only a mod or admin can run this command.'),
			glados.Help('ponylist', '<subreddit>', "pm's you a list of emotes in the specefied subreddits, or sends a list of all subreddits if empty.")
		]
		
	def EvaluateEmotePath(self, Emote):
		Closest = "";
		CloseDis = 0;
		r = difflib.get_close_matches(Emote, self.RawEmoteList, 1, 0.2);
		if len(r)>0:
			return r[0];
		return "";

	@staticmethod
	def __concat_into_valid_message(list_of_strings):
		ret = list()
		temp = list()
		l = 0
		max_length = 1000

		if len(list_of_strings) == 0:
			return ret

		for s in list_of_strings:
			l += len(s)
			if l >= max_length:
				ret.append('\n'.join(temp))
				l = 0
				temp = list()
			temp.append(s)
		ret.append('\n'.join(temp))
		return ret
		
	@glados.Module.commands('pony')
	def request_pony_emote(self, message, content):
		Path = self.emotes_path+content.replace('/','').replace('\\','').replace('.','');
		Found = False;
		if content == '':
			yield from self.provide_help('pony', message)
			return
		if isfile(Path+".png"):
			Path = Path+".png";
			Found = True;
		if not Found and isfile(Path+".gif"):
			Path = Path+".gif";
			Found=True;
		if not Found:
			Name = self.EvaluateEmotePath(content);
			if Name!='':
				yield from self.client.send_message(message.channel, 'Unknown emoticon (did you mean: '+Name+"?)")
			else:
				yield from self.client.send_message(message.channel, 'Unknown emoticon.');
			return
		
		yield from self.client.send_file(message.channel, Path)

	@glados.Module.commands('ponydel')
	def delete_pony_emote(self, message, content):
		Path = self.emotes_path+content.replace('/','').replace('\\','').replace('.','');
		Found = False;
		if(content==''):
			yield from self.provide_help('ponydel', message);
			return;
		if isfile(Path+".png"):
			Path = Path+".png";
			Found = True;
		if not Found and isfile(Path+".gif"):
			Path = Path+".gif";
			Found=True;
		if not Found:
			Name, Res = self.EvaluateEmotePath(content);
			yield from self.client.send_message(message.channel, 'Unknown emoticon (did you mean: '+Name+"?)")
			return
		os.remove(Path);
		yield from self.client.send_message(message.channel, 'Deleted emote from db.');
		
	@glados.Module.commands('ponylist')
	def get_pony_list(self, message, content):
		Response = [];
		if content=='':
			Response.append("List of available subreddits:");
			for key, items in self.EmoteList.items():
				Response.append(key);
		else:
			Sub = self.EmoteList.get(content);
			if not Sub:
				Response.sppend("Unknown subreddit.");
			else:
				Response.append("List of emotes for "+content);
				for key, items in Sub.items():
					Response.append(key);
		List = self.__concat_into_valid_message(Response);
		for msg in List:
			yield from self.client.send_message(message.author, msg);