import discord
from discord.ext import commands
from config import TOKEN
import os

# Setup intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# Create bot instance
bot = commands.Bot(command_prefix="$", intents=intents)

# When bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

# Load all command cogs from the 'commands' folder
@bot.event
async def setup_hook():
    for filename in os.listdir("./commands"):
        if filename.endswith(".py") and filename != "__init__.py":
            await bot.load_extension(f"commands.{filename[:-3]}")

# Example command
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# Run bot
bot.run(TOKEN)
