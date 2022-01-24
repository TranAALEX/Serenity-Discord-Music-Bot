import discord
import os
import urllib.parse
import urllib.request
import re
import asyncio
import pytube
from bs4 import BeautifulSoup
import requests
from discord.ext import commands

#--------------UTILITIES---------------#
class Audio:
	def __init__(self, client, ctx=None, message=None):
		self.client = client
		self.message = message
		self.ctx = ctx
		self.audio_library = os.path.join("./SerenityDB", "AudioLibrary")
		try:
			self.voice_channel = discord.utils.get(self.client.voice_clients, guild=self.ctx.guild)
			print(self.voice_channel)
		except:
			self.voice_channel = discord.utils.get(self.client.voice_clients, guild=message.guild)

	async def connect(self):
		voice_channel = self.ctx.author.voice.channel
		await voice_channel.connect()

	async def disconnect(self):
		await self.voice_channel.disconnect()

	def stop(self):
		self.voice_channel.stop()

	def is_playing(self):
		return self.voice_channel.is_playing()

	def play_audio(self, filename, delete_after=None):
		audio_source = discord.FFmpegPCMAudio(filename)
		if delete_after == None:
			self.voice_channel.play(audio_source, after=None)
		elif delete_after != None:
			self.voice_channel.play(audio_source, after=delete_after)


#-------------------WORKER-------------------#
class Leave:
	def __init__(self, client, ctx):
		self.ctx = ctx
		self.client = client

	async def main(self):
		try:
			await Audio(self.client, self.ctx).disconnect()
		except:
			await Audio(self.client, self.ctx).connect()
			await Audio(self.client, self.ctx).disconnect()


class Play:
	def __init__(self, client, ctx, song_queue, arg1):
		self.ctx = ctx
		self.client = client
		self.song_queue = song_queue
		self.video_ctx = " ".join(arg1)
		self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

	def format_search_results(self):
		query_string = urllib.parse.urlencode({'search_query': self.song_queue[0]})
		html_content = urllib.request.urlopen("http://www.youtube.com/results?" + query_string)
		search_results = re.findall(r"watch\?v=(\S{11})", html_content.read().decode())
		return search_results
	
	def download_source(self,search_results):
		yt = pytube.YouTube(f"https://www.youtube.com/watch?v={search_results[0]}")
		video = yt.streams.get_audio_only()
		source = discord.FFmpegPCMAudio(video.url, **self.FFMPEG_OPTIONS)
		return video, source

	async def check_queue(self,e):
		try:
			self.song_queue.pop(0)
		except IndexError:
			pass
		if len(self.song_queue) != 0:
			search_results = self.format_search_results()
			video, source = self.download_source(search_results)
			self.ctx.voice_client.play(source,after=lambda e: self.check_queue(e))
			await self.ctx.send(f"Now playing {video.name}")
		else:
			pass

	async def main(self):
		try:
			await self.ctx.author.voice.channel.connect()
		except:
			pass
		if len(self.song_queue) == 0:
			self.song_queue.append(self.video_ctx)
			search_results = self.format_search_results()
			video, source = self.download_source(search_results)
			self.ctx.voice_client.play(source,after=lambda e: await self.check_queue(e))
			self.ctx.send(f"Now playing {video.name}")
		else:
			self.song_queue.append(self.video_ctx)
			await self.ctx.send(f"Song added to queue.")


class Skip:
	def __init__(self,client,ctx):
		self.client = client
		self.ctx = ctx

	async def main(self):
		self.ctx.voice_client.stop()
		self.ctx.send("Skipping current song.")
		

class Stop:
	def __init__(self,client,ctx,song_queue):
		self.ctx = ctx
		self.client = client
		self.song_queue = song_queue
  
	async def main(self):
		self.song_queue.clear()
		self.ctx.voice_client.stop()


class Pause:
	def __init__(self,client,ctx):
		self.client = client
		self.ctx = ctx

	async def main(self):
		self.ctx.voice_client.pause()


class Resume:
	def __init__(self,client,ctx):
		self.client = client
		self.ctx = ctx
	
	async def main(self):
		self.ctx.voice_client.resume()

class Queue:
	def __init__(self,client,ctx,song_queue):
		self.client = client
		self.ctx = ctx
		self.song_queue = song_queue

	def format_search_results(self):
		for song in self.song_queue:
			query_string = urllib.parse.urlencode({'search_query': song})
			html_content = urllib.request.urlopen("http://www.youtube.com/results?" + query_string)
			search_results = re.findall(r"watch\?v=(\S{11})", html_content.read().decode())
			yield search_results

	def format_queue(self):
		queue_string = ""
		for i,urls in enumerate(self.format_search_results()):
			page = requests.get(urls)
			soup = BeautifulSoup(page.content, "html.parser")
			queue_string += f"{i}. {soup.find('title').text}\n"
		return queue_string
    

	def format_embed(self):
		embed = discord.Embed(title="Queue", desc=self.format_queue)
		return embed

	async def main(self):
		embed = self.format_embed()
		await self.ctx.send(embed=embed)
	

#----------------RUNNER----------------------#
class Voice(commands.Cog):
	def __init__(self,client): 
		self.client = client
		self.song_queue = []
	
	@commands.command(aliases=[])
	async def leave(self,ctx):
		await Leave(self.client,ctx).main()
	
	@commands.command(aliases=[]) 
	async def stop(self,ctx):
		await Stop(self.client,ctx,self.song_queue).main()
	
	@commands.command(aliases=[]) 
	async def skip(self,ctx):
		await Skip(self.client,ctx).main()
	
	@commands.command(aliases=[])
	async def play(self,ctx,*arg1):
		await Play(self.client,ctx,self.song_queue,arg1).main()

	@commands.command(aliases=[])
	async def pause(self,ctx):
		await Pause(self.client,ctx).main()

	@commands.command(aliases=[])
	async def resume(self,ctx):
		await Resume(self.client,ctx).main()
		
	@commands.command(aliases=[])
	async def queue(self,ctx):
		await Queue(ctx,client,self.song_queue).main()

def setup(client):  
	client.add_cog(Voice(client))
	print("[Voice.py] loaded.")
