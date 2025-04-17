import discord
from discord.ext import commands
from config import TOKEN, GUILD_ID, ROLE_ID, VANITY_LINK, LOG_CHANNEL_ID
import random
import asyncio
import datetime
from flask import Flask
from threading import Thread

# Flask setup
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def start_flask():
    thread = Thread(target=run_flask)
    thread.start()

# Start Flask server
start_flask()

# Discord setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="$", intents=intents)
afks = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def ship(ctx, user1: discord.Member, user2: discord.Member):
    percent = random.randint(0, 100)
    hearts = "❤️" * (percent // 20) or "💔"
    nickname = ""
    if percent >= 50:
        nickname = random.choice(["TwinFlames", "CutiePies", "LoveBirds", "PowerDuo"])
        await ctx.send(f"💘 {user1.display_name} x {user2.display_name} 💘\nCompatibility: {percent}% {hearts}\nNickname: **{nickname}**")
    else:
        await ctx.send(f"💘 {user1.display_name} x {user2.display_name} 💘\nCompatibility: {percent}% {hearts}")

@bot.command()
async def choose(ctx, *, choices):
    options = choices.split(",")
    if len(options) < 2:
        await ctx.send("Please provide at least two choices separated by commas.")
    else:
        selected = random.choice(options).strip()
        await ctx.send(f"🎲 I choose: **{selected}**")

@bot.command()
async def afk(ctx, *, reason="AFK"):
    afks[ctx.author.id] = reason
    await ctx.send(f"🛑 {ctx.author.display_name} is now AFK: {reason}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id in afks:
        del afks[message.author.id]
        await message.channel.send(f"👋 Welcome back, {message.author.mention}! I removed your AFK.")

    for user_id in afks:
        if f"<@{user_id}>" in message.content:
            reason = afks[user_id]
            await message.channel.send(f"💤 That user is AFK: {reason}")
            break

    await bot.process_commands(message)

@bot.event
async def on_member_update(before, after):
    if not before or not after:
        return

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if not log_channel:
        return

    try:
        if before.bio != after.bio:
            if VANITY_LINK in (after.bio or "") and VANITY_LINK not in (before.bio or ""):
                await log_channel.send(f"🔗 {after.mention} added the vanity link to their bio!")
            elif VANITY_LINK in (before.bio or "") and VANITY_LINK not in (after.bio or ""):
                await log_channel.send(f"❌ {after.mention} removed the vanity link from their bio!")
    except Exception as e:
        print(f"Error checking bio change: {e}")

bot.run(TOKEN)
