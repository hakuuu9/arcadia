import discord
from discord.ext import commands
import random
import asyncio
from config import TOKEN, GUILD_ID, ROLE_ID, VANITY_LINK, LOG_CHANNEL_ID
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix="$", intents=intents)

afk_users = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(e)

# VANITY LINK ROLE MANAGEMENT WITH LOGGING
@bot.event
async def on_presence_update(before, after):
    member = after
    try:
        status = None
        if after.activities:
            for activity in after.activities:
                if activity.type == discord.ActivityType.custom:
                    status = activity.state
                    break

        has_link = status and VANITY_LINK in status
        has_role = ROLE_ID in [role.id for role in member.roles]

        channel = bot.get_channel(LOG_CHANNEL_ID)

        if has_link and not has_role:
            await member.add_roles(discord.Object(id=ROLE_ID))
            if channel:
                await channel.send(f"✅ Added role to {member.mention} for having the vanity link in their status.")
        elif not has_link and has_role:
            await member.remove_roles(discord.Object(id=ROLE_ID))
            if channel:
                await channel.send(f"❌ Removed role from {member.mention} for removing the vanity link from their status.")
    except Exception as e:
        print(f"Error in presence_update: {e}")

# AVATAR
@bot.command()
async def avatar(ctx, user: discord.User = None):
    user = user or ctx.author
    await ctx.send(user.display_avatar.url)

# AFK
@bot.command()
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.send(f"🛑 {ctx.author.display_name} is now AFK: {reason}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id in afk_users:
        del afk_users[message.author.id]
        await message.channel.send(f"👋 Welcome back, {message.author.mention}! I removed your AFK.")

    for user_id, reason in afk_users.items():
        if f"<@{user_id}>" in message.content:
            await message.channel.send(f"💤 That user is AFK: {reason}")
            break

    await bot.process_commands(message)

# SHIP
@bot.command()
async def ship(ctx, user1: discord.Member, user2: discord.Member):
    percent = random.randint(0, 100)
    message = f"**{user1.display_name}** + **{user2.display_name}** = **{percent}%**"
    if percent >= 50:
        nicknames = ["Sweethearts", "Power Couple", "Tortolitos", "Lovebirds"]
        nickname = random.choice(nicknames)
        message += f"\nThey are definitely **{nickname}**!"
    await ctx.send(message)

# 8BALL
@bot.command(name="8b")
async def eightball(ctx, *, question):
    responses = [
        "Yes", "No", "Maybe", "Definitely", "Absolutely not", "Ask again later",
        "Without a doubt", "Don't count on it", "Signs point to yes", "Very doubtful"
    ]
    await ctx.send(f"🎱 **Question:** {question}\n**Answer:** {random.choice(responses)}")

# CHOOSE
@bot.command()
async def choose(ctx, *, options: str):
    choices = [opt.strip() for opt in options.split(",") if opt.strip()]
    if len(choices) < 2:
        await ctx.send("Please provide at least two choices separated by commas.")
        return
    selected = random.choice(choices)
    await ctx.send(f"🎲 I choose: **{selected}**")

# REMIND
@bot.command()
async def remind(ctx, time: str, *, message: str):
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    try:
        unit = time[-1]
        if unit not in units:
            raise ValueError()
        delay = int(time[:-1]) * units[unit]
        await ctx.send(f"⏰ Reminder set for **{time}** from now: {message}")
        await asyncio.sleep(delay)
        await ctx.send(f"🔔 {ctx.author.mention}, reminder: **{message}**")
    except:
        await ctx.send("Invalid time format! Use formats like `10s`, `5m`, `1h`, or `2d`.")

# Keep the bot alive on Render
keep_alive()
bot.run(TOKEN)
