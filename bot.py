
import discord
from discord.ext import commands, tasks
import random
import asyncio
import re
from config import TOKEN, GUILD_ID, ROLE_ID, VANITY_LINK, LOG_CHANNEL_ID

intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is now online!")

@bot.event
async def on_presence_update(before, after):
    member = after if isinstance(after, discord.Member) else None
    if not member:
        return

    status_text = str(after.activity.name).lower() if after.activity else ""
    if VANITY_LINK in status_text:
        if ROLE_ID not in [role.id for role in member.roles]:
            role = member.guild.get_role(ROLE_ID)
            await member.add_roles(role)
            channel = bot.get_channel(LOG_CHANNEL_ID)
            await channel.send(f"✅ {member.mention} added the vanity link in status. Role given.")
    else:
        if ROLE_ID in [role.id for role in member.roles]:
            role = member.guild.get_role(ROLE_ID)
            await member.remove_roles(role)
            channel = bot.get_channel(LOG_CHANNEL_ID)
            await channel.send(f"❌ {member.mention} removed the vanity link from status. Role removed.")

@bot.command()
async def afk(ctx, *, reason="AFK"):
    await ctx.send(f"{ctx.author.mention} is now AFK: {reason}")

@bot.command()
async def avatar(ctx, user: discord.User = None):
    user = user or ctx.author
    await ctx.send(f"{user.name}'s avatar:\n{user.avatar.url}")

@bot.command()
async def ship(ctx, user1: discord.Member, user2: discord.Member):
    percentage = random.randint(0, 100)
    message = f"❤️ | {user1.display_name} × {user2.display_name}\nCompatibility: **{percentage}%**"

    if percentage >= 50:
        nicknames = ["Lovebirds", "Soulmates", "Turtledoves", "Power Couple", "Ultimate Duo"]
        nickname = random.choice(nicknames)
        message += f"\n💖 Couple Nickname: **{nickname}**"

    await ctx.send(message)

@bot.command(name="8b")
async def eight_ball(ctx, *, question):
    responses = [
        "Yes", "No", "Maybe", "Definitely", "Absolutely not", "Ask again later",
        "I'm not sure", "You can count on it", "Unlikely", "Certainly"
    ]
    await ctx.send(f"🎱 {random.choice(responses)}")

@bot.command()
async def remind(ctx, time: str, *, reminder: str):
    seconds = 0
    time = time.lower()

    matches = re.match(r"(\d+)([smh])", time)
    if not matches:
        await ctx.send("❌ Format should be like `10s`, `5m`, or `1hr`.")
        return

    amount, unit = matches.groups()
    amount = int(amount)

    if unit == "s":
        seconds = amount
    elif unit == "m":
        seconds = amount * 60
    elif unit == "h":
        seconds = amount * 3600

    await ctx.send(f"⏰ Okay {ctx.author.mention}, I’ll remind you in {time}.")

    await asyncio.sleep(seconds)
    await ctx.send(f"🔔 Reminder for {ctx.author.mention}: {reminder}")

bot.run(TOKEN)
