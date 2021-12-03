import discord
import os
from discord.ext import commands

client = commands.Bot(command_prefix="-", intents=discord.Intents.all())
client.remove_command("help")

@client.event
async def on_ready():
	cogfolder = os.listdir("./Cogs")
	for filename in cogfolder:
		if filename.endswith(".py"):
			client.load_extension(f"Cogs.{filename[:-3]}")
	activity = discord.Game("-help",type=3)
	await client.change_presence(status=discord.Status.online,activity=activity)
	print("Serenity bot ready.")

@client.command()
async def unload(ctx,extension):
  client.unload_extension(f"Cogs.{extension}")

@client.command()
async def load(ctx,extension):
  client.load_extension(f"Cogs.{extension}")

@client.command()
async def stream_announce(ctx):
  activity = discord.Streaming(name=ctx.message.content,url=None)
  await client.change_presence(status=discord.Status.online,activity=activity)

if __name__ == "__main__":
	client.run(os.environ["SMB_TOKEN"])
