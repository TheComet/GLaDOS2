import glados
import os
from os import listdir
from os.path import isfile, join
import json;
import asyncio;
import urllib.request;
import sys;
import threading;
from PIL import Image;
import imageio;
import apng2gif;
import time;

class EEmote:
	Name = "";
	ImgPath = "";
	xOffset = 0;
	yOffset = 0;
	xSize = 0;
	ySize = 0;
	Flip = False;
	
	def __init__(self, Name, ImgPath, xOffset, yOffset, xSize, ySize, Flip):
		self.Name = Name;
		self.ImgPath = ImgPath;
		self.xOffset = xOffset;
		self.yOffset = yOffset;
		self.xSize = xSize;
		self.ySize = ySize;
		self.Flip = Flip;

class BuildEmotes(glados.Module):
	emotedb_path = 'modules/pony/emotesdb/';
	configdb_path = 'modules/pony/dbconfig/';
	WorkerThreads = 8;
	BuildingDB = "";
	IsRunning = False;

	def __init__(self):
		super(BuildEmotes, self).__init__()
		return;
		
	def get_help_list(self):
		return [
			glados.Help('buildpony', '<Optional db space sperated list>', 'Mod only usable, use to rebuild the entire pony emote db, or only a partial db specefied by Opetiondb(i.e: mylittlepony only builds for the mylittlepony.json db)')
		]
		
	def SaveTargetImage(self, Source, Name, xOffset, yOffset, xSize, ySize, Flip, Convert):
		mImg = Image.open(Source);
		mImg = mImg.crop((xOffset, yOffset, xOffset+xSize, yOffset+ySize));
		if Flip is True: 
			mImg = mImg.transpose(Image.FLIP_LEFT_RIGHT);
		if Convert is True:
			mImg.load();
			Alpha = mImg.split()[-1];
			mImg = mImg.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255);
			mask = Image.eval(Alpha, lambda a:255 if a<=128 else 0)
			mImg.paste(255, mask);
			mImg.save(self.emotedb_path+Name+".png", transparency=255, optimize=True);
		else:
			mImg.save(self.emotedb_path+Name+".png", optimize=True);
			
	def BuildEmote(self, name, ImagePath, xOffset, yOffset, xSize, ySize, Flip):
		#print("Emote: '"+name+"' Img: "+ImagePath+" o: "+str(xOffset)+" "+str(yOffset)+" s: "+str(xSize)+" "+str(ySize));
		NameBase = name+".tmp";
		FrameCnt = 1;
		try:
			urllib.request.urlretrieve(ImagePath, NameBase);
			FrameCnt = apng2gif.convert(NameBase, self.emotedb_path+name+".gif", xOffset, yOffset, xSize, ySize, Flip);
			if(FrameCnt==1):
				#we baked into the function the ability not to save if there is only 1 frame, so we can save it as a png instead.
				self.SaveTargetImage(NameBase, name, xOffset, yOffset, xSize, ySize, Flip, True);
				
		except Exception as e:
			if(str(e)=="bad transparency mask"):
				try:
					#save as regular file instead.
					self.SaveTargetImage(NameBase, name, xOffset, yOffset, xSize, ySize, Flip, False);
				except Exception as e2:
					print("Error2 processing emote: "+name);
					print(e);
				
			else:
				print("Error processing emote: "+name);
				print(e);

			
		
		for i in range(0,3): #retry a few times in case failure is due to the os hasn't given up a handle right away.
			try:
				os.remove(NameBase);
				break;
			except:
				time.sleep(1);
	
	def BuildEmoteDB(self, DataSet):
		for e in DataSet:
			self.BuildEmote(e.Name, e.ImgPath, e.xOffset, e.yOffset, e.xSize, e.ySize, e.Flip);
			
	def BuildDB(self, dbname):
		DataSet = [];
		for i in range(0,self.WorkerThreads):
			DataSet.append([]);
		
		path = self.configdb_path+dbname+".json";
		if not isfile(path):
			print("Unknown db: "+dbname);
			return;
		self.BuildingDB = dbname;
		print("Building db: "+dbname);
		JSON_File = open(path).read();
		JSON = json.loads(JSON_File);
		i = 0;
		for key, items in JSON.items():
			Name = key[1:].replace('/','').replace('\\','').replace('.','');
			Emote = items.get("Emotes");
			if not Emote: continue;
			Emote = Emote.get("");
			if not Emote: continue;
			Img = Emote.get("Image");
			Offset = Emote.get("Offset");
			Size = Emote.get("Size");
			CTransform = None;
			if(Emote.get("CSS")): CTransform = Emote["CSS"].get("transform");
			Flip = False;
			xOffset = 0;
			yOffset = 0;
			xSize = 0;
			ySize = 0;
			if not Img:
				continue;
			if Offset:
				xOffset = -Offset[0];
				yOffset = -Offset[1];
			if Size:
				xSize = Size[0];
				ySize = Size[1];
			if CTransform:
				Flip = True; #this is real dumb right now, but later i hope to actually parse and see if there is any interesting transform affects on emotes, but for now xScale seems to be the most common.
			DataSet[i].append(EEmote(Name, "https:"+Img, xOffset, yOffset, xSize, ySize, Flip));
			i = (i+1)%self.WorkerThreads;
			#self.BuildEmote(Name, "https:"+Img, xOffset, yOffset, xSize, ySize, Flip);
		Thrs = [];
		for x in range(0, self.WorkerThreads):
			T = threading.Thread(target=self.BuildEmoteDB, args = (DataSet[x],));
			T.start();
			Thrs.append(T);
		for t in Thrs:
			t.join();
		print("Finished building: "+dbname);
		#yield from self.client.send_message(message.channel, 'Finished building db: '+dbname);
		return;
	
	def RunThread(self, content):
		self.IsRunning = True;
		try:
			if(content==''):
				Files = [f for f in listdir(self.configdb_path) if isfile(join(self.configdb_path, f))];
				for f in Files:
					self.BuildDB(os.path.splitext(f)[0]);
				self.IsRunning = False;
				print("Finished thread!");
				return;
			Databases = content.split(' ');
			for db in Databases:
				self.BuildDB(db);
		except Exception as e:
			print("Exception during thread: ");
			print(e);
		self.IsRunning=False;
		print("Finished thread!");
		return;
		
	@glados.Module.commands('buildpony')
	def build_ponydb(self, message, content):
		if message.author.id not in self.settings['moderators']['IDs'] and message.author.id not in self.settings['admins']['IDs']:
			yield from self.client.send_message(message.channel, "This command can only be ran by a mod, or admin.");
			return;
		#since this is a long process, we will spawn a thread to do the work in to not tie of the bot.
		if(self.IsRunning is True):
			yield from self.client.send_message(message.channel, "Database is currently building: "+self.BuildingDB);
			return;
		yield from self.client.send_message(message.channel, 'Building pony database...this may take awhile.');
			
		Thread = threading.Thread(target=self.RunThread, args=(content,));
		Thread.daemon= True;
		Thread.start();
		return;
