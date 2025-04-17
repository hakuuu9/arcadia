import discord
from discord.ext import commands
from keep_alive import run  # Import the function to run Flask

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="$", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Start the Flask app in the background
import threading
threading.Thread(target=run).start()

bot.run('YOUR_BOT_TOKEN')
