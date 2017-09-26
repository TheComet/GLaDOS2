import glados
import os
from os import listdir
from os.path import isfile
import json
import difflib
import threading
import APNGLib
import time
import urllib.request
import sys
from PIL import Image

class eemote:
	def __init__(self, name, image_path, x_offset, y_offset, x_size, y_size, flip, is_nsfw):
		self.name = name
		self.image_path = image_path
		self.x_offset = x_offset
		self.y_offset = y_offset
		self.x_size = x_size
		self.y_size = y_size
		self.flip = flip
		self.is_nsfw = is_nsfw

class emotes(glados.Module):
		
	def setup_global(self):
		self.emotes_path = 'modules/pony/emotesdb/'
		self.infodb_path = 'modules/pony/emote_info_db/'
		self.tagdb_path = 'modules/pony/emote_tag_db/'
		self.tag_list = {}
		self.emote_list = {}
		self.raw_emote_list = []
		self.is_running = True
		thread = threading.Thread(target=self.build_emote_db, args=())
		thread.start()
		return
	
	def setup_memory(self):
		mem = self.get_memory()
		mem['blacklist'] = {}
		mem['blacklist']['allow_nsfw'] = False
		mem['config_path'] = self.get_config_dir()+"/emotes.json"
		self.load_blacklist()
		
	def load_blacklist(self):
		mem = self.get_memory()
		if isfile(mem['config_path']):
			mem['blacklist'] = json.loads(open(mem['config_path']).read())
	
	def save_blacklist(self):
		mem = self.get_memory()
		try:
			os.makedirs(os.path.dirname(mem['config_path']))
		except Exception as E:
			if "File exists" not in str(E):
				print(E)
				return
			#do nothing as the dirs probably already exist
		f = open(mem['config_path'], "w")
		if f:
			f.write(json.dumps(mem['blacklist']))
			
	def save_target_image(self, source, name, x_offset, y_offset, x_size, y_size, flip, convert):
		m_img = Image.open(source)
		m_img = m_img.crop((x_offset, y_offset, x_offset + x_size, y_offset + y_size))
		if flip is True: 
			m_img = m_img.transpose(Image.FLIP_LEFT_RIGHT)
		if convert is True:
			m_img.load()
			alpha = m_img.split()[ - 1]
			m_img = m_img.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
			mask = Image.eval(alpha, lambda a:255 if a<=128 else 0)
			m_img.paste(255, mask)
			m_img.save(self.emotes_path + name + ".png", transparency=255, optimize=True)
		else:
			m_img.save(self.emotes_path + name + ".png", optimize=True)
			
	def build_emote(self, name, image_path, x_offset, y_offset, x_size, y_size, flip):
		#print("Emote: '" + name + "' Img: " + ImagePath + " o: " + str(xOffset) + " " + str(yOffset) + " s: " + str(xSize) + " " + str(ySize))
		name_base = name + ".tmp"
		frame_cnt = 1
		transform = APNGLib.TransformCrop | APNGLib.TransformNoGif1Frame
		if flip is True:
			transform |= APNGLib.TransformFlipHorizontal
		try:
			urllib.request.urlretrieve(image_path, name_base)
			frame_cnt = APNGLib.MakeGIF(name_base, self.emotes_path + name + ".gif", transform, x_offset, y_offset, x_size, y_size)
			if(frame_cnt==1):
				#we tell the function the  not to save if there is only 1 frame, so we can save it as a png instead.
				self.save_target_image(name_base, name, x_offset, y_offset, x_size, y_size, flip, True)
				
		except Exception as e:
			if(str(e)=="bad transparency mask"):
				try:
					#save as regular file instead.
					self.save_target_image(name_base, name, x_offset, y_offset, x_size, y_size, flip, False)
				except Exception as e2:
					print("Error2 processing emote: " + name)
					print(e2)
				
			else:
				print("Error processing emote: " + name)
				print(e)

			
		
		for i in range(0,3): #retry a few times in case failure is due to the os hasn't given up a handle right away.
			try:
				os.remove(name_base)
				break
			except:
				time.sleep(1)
				
	def build_emote_db(self):
		self.tag_list = {}
		self.emote_list = {}
		self.raw_emote_list = []
		files = [f for f in listdir(self.infodb_path) if isfile(self.infodb_path + f)]
		for f in files:
			subreddit = os.path.splitext(f)[0]
			jinfo_file = open(self.infodb_path + f)
			jtag_file = open(self.tagdb_path + f)
			jinfodata = json.loads(jinfo_file.read())
			jtagdata = json.loads(jtag_file.read())
			jinfo_file.close()
			jtag_file.close()
			self.tag_list[subreddit] = {}
			for key, items in jinfodata.items():
				name = key[1:].replace('/','').replace('\\','').replace('.','')
				emote = items.get("Emotes")
				if not emote: continue
				emote = emote.get("")
				if not emote: continue
				image_path = emote.get("Image")
				offset = emote.get("Offset")
				size = emote.get("Size")
				is_nsfw = False
				flip = False
				x_offset = 0
				y_offset = 0
				x_size = 0
				y_size = 0
				css_transform = None
				if(emote.get("CSS")): css_transform = emote["CSS"].get("transform")
				if not image_path:
					continue
				if offset:
					x_offset =  - offset[0]
					y_offset =  - offset[1]
				if size:
					x_size = size[0]
					y_size = size[1]
				if css_transform:
					flip = True #this is real dumb right now, but later i hope to actually parse and see if there is any interesting transform affects on emotes, but for now xScale seems to be the most common.
				self.tag_list[subreddit][name] = ""
				tags = jtagdata.get(key)
				if tags:
					for tag in tags:
						if not self.tag_list.get(tag):
							self.tag_list[tag] = {}
						self.tag_list[tag][name] = ""
						if tag=="+nsfw":
							is_nsfw=True
				if not self.emote_list.get(name):
					self.emote_list[name] = eemote(name, "https://"+image_path.split('//')[1], x_offset, y_offset, x_size, y_size, flip, is_nsfw)
					self.raw_emote_list.append(name)
				
		self.is_running = False
		print("Finished building emote db.")
	
	def get_help_list(self):
		return [
			glados.Help('pony', '<emote>', 'Shows a pony with the specified emotion. '
                                           'Search https://ponymotes.net/view/ to find an emote or use ponylist command(note: not all emotes are supported)'),
			glados.Help('ponydel', '<emote>', 'blacklists the specified pony emote from the database for that server, only a mod or admin can run this command.'),
			glados.Help('ponyundel', '<emote>', 'unblacklists the specified pony emote from the database for that server, only a mod or admin can run this command.'),
			glados.Help('ponynsfw', '<enable/disable>', 'sets a flag allowing or disallowing nsfw emotes on the specefied server, only a mod or admin can run this command.'),
			glados.Help('ponylist', '<subreddit | tags>', "pm's you a list of emotes in the specefied subreddits, or tagged emotes(i.e: +v) or sends a list of all subreddits if empty.")
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
				l = len(s)
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
		
	
	@glados.Module.commands('pony')
	def request_pony_emote(self, message, content):
		
		if not content:
			yield from self.provide_help('pony', message)
			return
		
		emote = self.emote_list.get(content)
		if not emote:
			name = self.spellcheck_emote_name(content)
			if name:
				yield from self.client.send_message(message.channel, 'Unknown emoticon (did you mean: ' + name + "?)")
			else:
				yield from self.client.send_message(message.channel, 'Unknown emoticon.')
			return

		mem = self.get_memory()
		if mem['blacklist'].get(emote.name):
			yield from self.client.send_message(message.channel, 'Emote is blacklisted on this server.')
			return
		if not mem['blacklist']['allow_nsfw'] and emote.is_nsfw:
			yield from self.client.send_message(message.channel, 'Emote is tagged as nsfw.')
			return
		
		path = self.find_emote_path(emote.name)
		if not path:
			self.build_emote(emote.name, emote.image_path, emote.x_offset, emote.y_offset, emote.x_size, emote.y_size, emote.flip)
			path = self.find_emote_path(emote.name)
		if not path:
			yield from self.client.send_message(message.channel, "Emote doesn't work")
			return
		yield from self.client.send_file(message.channel, path)

	@glados.Module.commands('ponydel')
	def delete_pony_emote(self, message, content):
		if message.author.id not in self.settings['moderators']['IDs'] and message.author.id not in self.settings['admins']['IDs']:
			yield from self.client.send_message(message.channel, "This command can only be ran by a mod, or admin.")
			return
		if not content:
			yield from self.provide_help('ponydel', message)
			return
		
		emote = self.emote_list.get(content)
		if not emote:
			name = self.spellcheck_emote_name(content)
			if name:
				yield from self.client.send_message(message.channel, 'Unknown emoticon (did you mean: ' + name + "?)")
			else:
				yield from self.client.send_message(message.channel, 'Unknown emoticon.')
			return
		
		mem = self.get_memory()
		mem['blacklist'][emote.name] = ""
		
		self.save_blacklist()
		yield from self.client.send_message(message.channel, 'blacklisted emote.')
	
	@glados.Module.commands('ponyundel')
	def undelete_pony_emote(self, message, content):
		if message.author.id not in self.settings['moderators']['IDs'] and message.author.id not in self.settings['admins']['IDs']:
			yield from self.client.send_message(message.channel, "This command can only be ran by a mod, or admin.")
			return
		if not content:
			yield from self.provide_help('ponyundel', message)
			return
		
		emote = self.emote_list.get(content)
		if not emote:
			name = self.spellcheck_emote_name(content)
			if name:
				yield from self.client.send_message(message.channel, 'Unknown emoticon (did you mean: ' + name + "?)")
			else:
				yield from self.client.send_message(message.channel, 'Unknown emoticon.')
			return
		
		mem = self.get_memory()
		mem['blacklist'].pop(emote.name, None)
		self.save_blacklist()
		yield from self.client.send_message(message.channel, 'removed emote from blacklist.')
	
	@glados.Module.commands('ponynsfw')
	def pony_nsfw(self, message, content):
		if message.author.id not in self.settings['moderators']['IDs'] and message.author.id not in self.settings['admins']['IDs']:
			yield from self.client.send_message(message.channel, "This command can only be ran by a mod, or admin.")
			return
		if not content or (content != "enable" and content != "disable"):
			yield from self.provide_help('ponynsfw', message)
			return
		enable = content=="enable"
		mem = self.get_memory()
		mem['blacklist']['allow_nsfw'] = enable
		self.save_blacklist()
		if enable:
			yield from self.client.send_message(message.channel, 'nsfw emotes have been enabled.')
		else:
			yield from self.client.send_message(message.channel, 'nsfw emotes have been disabled.')
		return
		
	@glados.Module.commands('ponylist')
	def get_pony_list(self, message, content):
		response = []
		temp = ""
		per_line = 25
		i = 0
		if not content:
			response.append("List of available tags to search through:")
			for key, items in self.tag_list.items():
				if i == 0:
					temp = key
				else:
					temp += " | " + key
				i += 1
				if i == per_line:
					response.append("``" + temp + "``")
					i = 0
			if i != 0:
				response.append("``" + temp + "``")
		else:
			tags = content.split()
			response.append("List of emotes which have any of the tags: " + content+"")
			for t in tags:
				tag_list = self.tag_list.get(t)
				if not tag_list:
					continue
				for key, items in tag_list.items():
					if i==0:
						temp = key
					else:
						temp += " | " + key
					i += 1
					if i == per_line:
						response.append("``" + temp + "``")
						i = 0
			if i != 0:
				response.append("``" + temp + "``")
		response.append('')
		rlist = self.__concat_into_valid_message(response)
		for msg in rlist:
			yield from self.client.send_message(message.author, msg)