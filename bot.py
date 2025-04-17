import discord
from discord.ext import commands
from config import TOKEN
from keep_alive import keep_alive
import os
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="$", intents=intents)

# Load commands from commands folder
for filename in os.listdir("./commands"):
    if filename.endswith(".py"):
        bot.load_extension(f"commands.{filename[:-3]}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

keep_alive()  # Starts Flask server
bot.run(TOKEN)
