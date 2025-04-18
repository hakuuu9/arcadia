import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
from config import TOKEN, GUILD_ID, ROLE_ID, VANITY_LINK, LOG_CHANNEL_ID
import random
import asyncio
import datetime
import re

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="$", intents=intents)

afk_users = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def ship(ctx: Context, user1: discord.Member, user2: discord.Member):
    percent = random.randint(0, 100)
    hearts = "❤️" * (percent // 20) or "💔"
    nicknames = ["Lovebirds", "Twin Flames", "Sweethearts", "Power Couple", "Perfect Pair"]
    description = f"**{user1.display_name}** 💞 **{user2.display_name}**\nCompatibility: **{percent}%** {hearts}"
    if percent >= 50:
        description += f"\nCouple Nickname: **{random.choice(nicknames)}**"
    await ctx.send(description)

@bot.command(name="8b")
async def eight_ball(ctx: Context, *, question: str):
    responses = [
        "Absolutely yes!",
        "No doubt about it.",
        "Maybe… time will tell.",
        "I wouldn’t count on it.",
        "Ask again later.",
        "It’s a mystery even to me.",
        "Definitely not.",
        "Seems likely!",
        "Highly questionable.",
        "You already know the answer."
    ]
    response = random.choice(responses)
    await ctx.send(f"🎱 **Question:** {question}\n**Answer:** {response}")

@bot.command()
async def remind(ctx: Context, time: str, *, message: str):
    time_pattern = r"(\d+)(s|m|h|d)"
    match = re.fullmatch(time_pattern, time.lower())
    if not match:
        await ctx.send("Invalid time format. Use formats like `10s`, `5m`, `1h`, or `2d`.")
        return

    amount, unit = int(match.group(1)), match.group(2)
    seconds = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
    wait_time = amount * seconds

    await ctx.send(f"⏰ I’ll remind you in **{time}** about: {message}")
    await asyncio.sleep(wait_time)
    await ctx.send(f"🔔 <@{ctx.author.id}> Reminder: {message}")

@bot.command()
async def afk(ctx: Context, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.send(f"🛑 {ctx.author.display_name} is now AFK: {reason}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id in afk_users:
        del afk_users[message.author.id]
        await message.channel.send(f"👋 Welcome back, {message.author.mention}! I removed your AFK.")

    for user_id in afk_users:
        if f"<@{user_id}>" in message.content:
            reason = afk_users[user_id]
            await message.channel.send(f"💤 That user is AFK: {reason}")
            break

    await bot.process_commands(message)

@bot.command()
async def choose(ctx: Context, *, options: str):
    items = [item.strip() for item in re.split(r",|\|", options) if item.strip()]
    if len(items) < 2:
        await ctx.send("Please provide at least two options separated by commas or `|`.")
    else:
        chosen = random.choice(items)
        await ctx.send(f"🎲 I choose: **{chosen}**")

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if not log_channel:
        return

    changes = []

    try:
        before_user_data = await bot.fetch_user(before.id)
        after_user_data = await bot.fetch_user(after.id)

        if before_user_data.bio != after_user_data.bio:
            before_bio = before_user_data.bio or "None"
            after_bio = after_user_data.bio or "None"
            changes.append(f"🧾 **Bio changed**\nBefore: `{before_bio}`\nAfter: `{after_bio}`")

            if VANITY_LINK in after_bio and VANITY_LINK not in before_bio:
                changes.append(f"🔗 **Vanity link added to bio!** ({VANITY_LINK})")
            elif VANITY_LINK in before_bio and VANITY_LINK not in after_bio:
                changes.append(f"❌ **Vanity link removed from bio!** ({VANITY_LINK})")

    except Exception as e:
        print(f"Error fetching user bio: {e}")

    if before.activity != after.activity:
        if isinstance(after.activity, discord.CustomActivity):
            before_status = before.activity.name if before.activity else "None"
            after_status = after.activity.name if after.activity else "None"
            changes.append(f"📝 **Custom Status changed**\nBefore: `{before_status}`\nAfter: `{after_status}`")

    if changes:
        embed = discord.Embed(
            title="🔔 Member Update",
            description=f"**User:** {after.mention} (`{after}`)\n**ID:** `{after.id}`",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.utcnow()
        )
        for change in changes:
            embed.add_field(name="Update", value=change, inline=False)
        await log_channel.send(embed=embed)

bot.run(TOKEN)
