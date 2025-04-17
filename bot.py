import discord
from discord.ext import commands
from config import TOKEN
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="$", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Load the cogs
bot.load_extension("cogs.ship")
bot.load_extension("cogs.remind")
bot.load_extension("cogs.choose")
bot.load_extension("cogs.afk")
bot.load_extension("cogs.vanity")

bot.run(TOKEN)
