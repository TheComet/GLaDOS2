import glados
import os
from os import listdir
from os.path import isfile
import json
import asyncio
import urllib.request
import sys
import threading
from PIL import Image
import APNGLib
import time

class eemote:
	def __init__(self, name, image_path, x_offset, y_offset, x_size, y_size, flip):
		self.name = name
		self.image_path = image_path
		self.x_offset = x_offset
		self.y_offset = y_offset
		self.x_size = x_size
		self.y_size = y_size
		self.flip = flip

class build_emotes(glados.Module):

	def setup_global(self):
		self.emotedb_path = 'modules/pony/emotesdb/'
		self.configdb_path = 'modules/pony/dbconfig/'
		self.worker_threads = 8
		self.building_db = ""
		self.is_running = False
		return
		
	def get_help_list(self):
		return [
			glados.Help('buildpony', '<Optional db space sperated list>', 'Mod only usable, use to rebuild the entire pony emote db, or only a partial db specefied by Opetiondb(i.e: mylittlepony only builds for the mylittlepony.json db)')
		]
		
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
			m_img.save(self.emotedb_path + name + ".png", transparency=255, optimize=True)
		else:
			m_img.save(self.emotedb_path + name + ".png", optimize=True)
			
	def build_emote(self, name, image_path, x_offset, y_offset, x_size, y_size, flip):
		#print("Emote: '" + name + "' Img: " + ImagePath + " o: " + str(xOffset) + " " + str(yOffset) + " s: " + str(xSize) + " " + str(ySize))
		name_base = name + ".tmp"
		frame_cnt = 1
		transform = APNGLib.TransformCrop | APNGLib.TransformNoGif1Frame
		if flip is True:
			transform |= APNGLib.TransformFlipHorizontal
		try:
			urllib.request.urlretrieve(image_path, name_base)
			frame_cnt = APNGLib.MakeGIF(name_base, self.emotedb_path + name + ".gif", transform, x_offset, y_offset, x_size, y_size)
			if(frame_cnt==1):
				#we tell the function the  not to save if there is only 1 frame, so we can save it as a png instead.
				self.save_target_image(name_base, name, x_offset, y_offset, x_size, y_size, flip, True)
				
		except Exception as e:
			if(str(e)=="bad transparency mask"):
				try:
					#save as regular file instead.
					self.save_target_image(NameBase, name, xOffset, yOffset, xSize, ySize, Flip, False)
				except Exception as e2:
					print("Error2 processing emote: " + name)
					print(e)
				
			else:
				print("Error processing emote: " + name)
				print(e)

			
		
		for i in range(0,3): #retry a few times in case failure is due to the os hasn't given up a handle right away.
			try:
				os.remove(name_base)
				break
			except:
				time.sleep(1)
	
	def build_emote_db(self, data_set):
		for e in data_set:
			self.build_emote(e.name, e.image_path, e.x_offset, e.y_offset, e.x_size, e.y_size, e.flip)
			
	def build_db(self, db_name):
		data_set = []
		for i in range(0,self.worker_threads):
			data_set.append([])
		
		path = self.configdb_path + db_name + ".json"
		if not isfile(path):
			print("Unknown db: " + db_name)
			return
		self.building_db = db_name
		print("Building db: " + db_name)
		json_file = open(path).read()
		jdata = json.loads(json_file)
		i = 0
		for key, items in jdata.items():
			#strip out any symbols from the name that'd allow file pathing.
			name = key[1:].replace('/','').replace('\\','').replace('.','')
			emote = items.get("Emotes")
			if not emote: continue
			emote = emote.get("")
			if not emote: continue
			image_path = emote.get("Image")
			offset = emote.get("Offset")
			size = emote.get("Size")
			css_transform = None
			if(emote.get("CSS")): css_transform = emote["CSS"].get("transform")
			flip = False
			x_offset = 0
			y_offset = 0
			x_size = 0
			y_size = 0
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
			data_set[i].append(eemote(name, "https:" + image_path, x_offset, y_offset, x_size, y_size, flip))
			i = (i + 1)%self.worker_threads
			#self.BuildEmote(Name, "https:" + Img, xOffset, yOffset, xSize, ySize, Flip)
		threads = []
		for x in range(0, self.worker_threads):
			t = threading.Thread(target=self.build_emote_db, args = (data_set[x],))
			t.start()
			threads.append(t)
		for t in threads:
			t.join()
		print("Finished building: " + db_name)
		return
	
	def run_thread(self, content):
		self.is_running = True
		try:
			if not content:
				files = [f for f in listdir(self.configdb_path) if isfile(self.configdb_path + f)]
				for f in files:
					self.build_db(os.path.splitext(f)[0])
				self.is_running = False
				print("Finished thread!")
				return
			databases = content.split(' ')
			for db in databases:
				self.build_db(db)
		except Exception as e:
			print("Exception during thread: ")
			print(e)
		self.is_running=False
		print("Finished thread!")
		return
		
	@glados.Module.commands('buildpony')
	def build_ponydb(self, message, content):
		if message.author.id not in self.settings['moderators']['IDs'] and message.author.id not in self.settings['admins']['IDs']:
			yield from self.client.send_message(message.channel, "This command can only be ran by a mod, or admin.")
			return
		#since this is a long process, we will spawn a thread to do the work in to not tie of the bot.
		if self.is_running is True:
			yield from self.client.send_message(message.channel, "Database is currently building: " + self.building_db)
			return
		yield from self.client.send_message(message.channel, 'Building pony database...this may take awhile.')
			
		thread = threading.Thread(target=self.run_thread, args=(content,))
		thread.daemon= True
		thread.start()
		return
