import discord
from discord.ext import commands
from config import TOKEN
from flask import Flask
from threading import Thread
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="$", intents=intents)

# Flask keep-alive server
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print("🔗 Flask server running for keep-alive.")

# Load all cogs
initial_extensions = [
    "cogs.afk",
    "cogs.choose",
    "cogs.eight_ball",
    "cogs.remind",
    "cogs.vanity"
]

for ext in initial_extensions:
    bot.load_extension(ext)

# Start Flask in a separate thread
Thread(target=run_flask).start()

bot.run(TOKEN)
