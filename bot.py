import discord
from discord.ext import commands, tasks
from discord.utils import get
import asyncio
import random
import re
import datetime
from config import TOKEN, GUILD_ID, ROLE_ID, VANITY_LINK, LOG_CHANNEL_ID

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="$", intents=intents)

afk_users = {}
reminders = []

@bot.event
async def on_ready():
    print(f"Bot is ready as {bot.user}")
    check_reminders.start()

# AFK command
@bot.command()
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.send(f"🟡 {ctx.author.mention} is now AFK: {reason}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id in afk_users:
        reason = afk_users.pop(message.author.id)
        await message.channel.send(f"🟢 Welcome back {message.author.mention}! I removed your AFK status. Reason was: {reason}")

    for user_id in afk_users:
        if f"<@{user_id}>" in message.content:
            user = await bot.fetch_user(user_id)
            await message.channel.send(f"💤 {user.name} is AFK: {afk_users[user_id]}")
    await bot.process_commands(message)

# 8Ball command
@bot.command(name="8b")
async def eight_ball(ctx, *, question):
    responses = [
        "Absolutely yes 🌟", "Certainly not ❌", "Maybe... 🤔", "Ask again later ⏳",
        "Of course! 😄", "No way! 😬", "Looks promising 👀", "Unlikely 🙃", "Yes 💯", "Definitely not 💀"
    ]
    answer = random.choice(responses)
    await ctx.send(f"🎱 **Question:** {question}\n**Answer:** {answer}")

# Ship command
@bot.command()
async def ship(ctx, user1: discord.Member, user2: discord.Member):
    percentage = random.randint(0, 100)
    heart = "💔" if percentage < 50 else "❤️"
    couple_names = [
        "TandemTropa", "HeartBeats", "LoveBuds", "PusoDuo", "ShipSquad", "CharmPair",
        "CutieCouple", "MoonStars", "SunsetSoulmates", "FluffMates"
    ]
    nickname = f"💞 Couple Nickname: **{random.choice(couple_names)}**" if percentage >= 50 else ""
    await ctx.send(f"💘 {user1.mention} × {user2.mention}\n💟 Compatibility: **{percentage}%** {heart}\n{nickname}")

# Avatar command
@bot.command()
async def avatar(ctx, user: discord.Member = None):
    user = user or ctx.author
    await ctx.send(f"{user.name}'s avatar: {user.display_avatar.url}")

# Reminder command
@bot.command()
async def remind(ctx, time: str, *, reminder: str):
    match = re.match(r"(\d+)([smhd])", time.lower())
    if not match:
        await ctx.send("⚠️ Invalid time format. Use formats like `10s`, `5m`, `1h`, or `1d`.")
        return

    amount, unit = match.groups()
    seconds = int(amount) * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
    remind_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)

    reminders.append((ctx.author.id, ctx.channel.id, reminder, remind_time))
    await ctx.send(f"⏰ Okay {ctx.author.mention}, I’ll remind you in {amount}{unit} to: **{reminder}**")

@tasks.loop(seconds=10)
async def check_reminders():
    now = datetime.datetime.utcnow()
    for reminder in reminders[:]:
        user_id, channel_id, text, remind_time = reminder
        if now >= remind_time:
            user = await bot.fetch_user(user_id)
            channel = bot.get_channel(channel_id)
            if channel:
                await channel.send(f"🔔 {user.mention}, reminder: **{text}**")
            reminders.remove(reminder)

bot.run(TOKEN)
