import discord
from discord.ext import commands
from config import TOKEN  # Make sure your config.py has: TOKEN = "your_token_here"

# Setup intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# Create bot instance with $ as prefix
bot = commands.Bot(command_prefix="$", intents=intents)

# When bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

# Example command to test
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# Run the bot
bot.run(TOKEN)
