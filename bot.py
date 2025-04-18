
import discord
from discord.ext import commands, tasks
import random
import asyncio
import re
from config import TOKEN, GUILD_ID, ROLE_ID, VANITY_LINK, LOG_CHANNEL_ID

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="$", intents=intents)

vanity_pattern = re.compile(r"(https?:\/\/)?(www\.)?(discord\.gg|discord\.com\/invite)\/" + re.escape(VANITY_LINK))

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_presence_update(before, after):
    if not isinstance(after, discord.Member):
        return

    member = after
    role = discord.utils.get(member.guild.roles, id=ROLE_ID)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    status_has_link = vanity_pattern.search(str(after.activity)) if after.activity else False

    try:
        bio = (await bot.fetch_user(member.id)).bio or ""
        bio_has_link = VANITY_LINK in bio
    except Exception as e:
        print(f"Error fetching bio in presence_update: {e}")
        bio_has_link = False

    has_link = status_has_link or bio_has_link

    if has_link and role not in member.roles:
        await member.add_roles(role)
        if log_channel:
            await log_channel.send(f"✅ Gave role to {member.mention} for using the vanity link.")
    elif not has_link and role in member.roles:
        await member.remove_roles(role)
        if log_channel:
            await log_channel.send(f"❌ Removed role from {member.mention} for removing the vanity link.")

# AFK Command
afk_users = {}

@bot.command()
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.send(f"{ctx.author.mention} is now AFK: {reason}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id in afk_users:
        del afk_users[message.author.id]
        await message.channel.send(f"Welcome back {message.author.mention}, you are no longer AFK.")

    for user in message.mentions:
        if user.id in afk_users:
            await message.channel.send(f"{user.name} is AFK: {afk_users[user.id]}")

    await bot.process_commands(message)

# Avatar Command
@bot.command()
async def avatar(ctx, user: discord.Member = None):
    user = user or ctx.author
    await ctx.send(f"{user.name}'s avatar: {user.avatar.url}")

# Ship Command
@bot.command()
async def ship(ctx, user1: discord.Member, user2: discord.Member):
    percentage = random.randint(1, 100)
    bar = "█" * (percentage // 10) + "░" * (10 - (percentage // 10))

    if percentage >= 50:
        nicknames = ["❤️ Cutie Pair", "💞 Power Couple", "💕 Sweethearts", "💘 Twin Flames", "✨ Lovey Doveys"]
        nickname = random.choice(nicknames)
        await ctx.send(
            f"**{user1.display_name}** x **{user2.display_name}**\n"
            f"Match: {percentage}% [{bar}]\n"
            f"Couple Nickname: **{nickname}**"
        )
    else:
        await ctx.send(
            f"**{user1.display_name}** x **{user2.display_name}**\n"
            f"Match: {percentage}% [{bar}]\n"
            f"Better luck next time!"
        )

# 8Ball Command
@bot.command()
async def eightball(ctx, *, question):
    responses = [
        "Yes", "No", "Maybe", "Definitely", "Absolutely not",
        "I'm not sure", "Try again later", "Without a doubt", "Probably", "I don't think so"
    ]
    await ctx.send(f"🎱 {random.choice(responses)}")

# Remind Command
@bot.command()
async def remind(ctx, time: int, *, reminder: str):
    await ctx.send(f"⏰ I’ll remind you in {time} seconds: **{reminder}**")
    await asyncio.sleep(time)
    await ctx.send(f"🔔 {ctx.author.mention}, reminder: **{reminder}**")

bot.run(TOKEN)
