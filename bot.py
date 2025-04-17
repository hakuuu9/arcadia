import discord
from discord.ext import commands, tasks
import random
import asyncio
import re
from config import TOKEN, GUILD_ID, ROLE_ID, VANITY_LINK, LOG_CHANNEL_ID

intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix='$', intents=intents)

afk_users = {}
couple_nicknames = ["Lovebirds", "Perfect Pair", "Dynamic Duo", "Soulmates", "Cutie Couple"]

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')

@bot.event
async def on_presence_update(before, after):
    try:
        member = after if isinstance(after, discord.Member) else None
        if not member or member.bot:
            return

        custom_status = next((a for a in member.activities if a.type == discord.ActivityType.custom), None)
        has_link_in_status = custom_status and VANITY_LINK in custom_status.state if custom_status else False
        role = discord.utils.get(member.guild.roles, id=ROLE_ID)
        channel = bot.get_channel(LOG_CHANNEL_ID)

        if has_link_in_status:
            if role not in member.roles:
                await member.add_roles(role)
                if channel:
                    await channel.send(f"✅ Added role to {member.mention} for having the link in status.")
        else:
            if role in member.roles:
                await member.remove_roles(role)
                if channel:
                    await channel.send(f"❌ Removed role from {member.mention} for removing the link.")
    except Exception as e:
        print(f"Error in presence_update: {e}")

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
        await message.channel.send(f"Welcome back, {message.author.mention}! I removed your AFK status.")

    for user_id, reason in afk_users.items():
        if str(user_id) in message.content:
            user = await bot.fetch_user(user_id)
            await message.channel.send(f"{user.name} is AFK: {reason}")

    await bot.process_commands(message)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(f"{member.mention}'s avatar:\n{member.avatar.url}")

@bot.command()
async def ship(ctx, user1: discord.Member, user2: discord.Member):
    percentage = random.randint(1, 100)
    result = f"**{user1.display_name}** x **{user2.display_name}** = **{percentage}%**"
    if percentage >= 50:
        result += f"\nCouple Nickname: **{random.choice(couple_nicknames)}**"
    await ctx.send(result)

@bot.command(aliases=['8ball'])
async def eightball(ctx, *, question):
    responses = [
        "Yes.", "No.", "Maybe.", "Definitely!", "Absolutely not.", "Ask again later.",
        "It is certain.", "Very doubtful.", "Without a doubt.", "Better not tell you now."
    ]
    await ctx.send(f"**Question:** {question}\n**Answer:** {random.choice(responses)}")

@bot.command()
async def remind(ctx, time: str = None, *, reminder: str = None):
    if not time or not reminder:
        return await ctx.send("⏰ Usage: `$remind [time] [reminder]` (e.g. `$remind 10m Take a break`)")

    time_pattern = re.match(r"(\d+)([smhd])", time.lower())
    if not time_pattern:
        return await ctx.send("❌ Invalid time format. Use `s`, `m`, `h`, or `d`.")

    amount, unit = time_pattern.groups()
    amount = int(amount)
    seconds = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[unit]

    await ctx.send(f"✅ Okay {ctx.author.mention}, I'll remind you in {amount}{unit}: `{reminder}`")
    await asyncio.sleep(amount * seconds)

    try:
        await ctx.author.send(f"⏰ Reminder: **{reminder}**")
    except discord.Forbidden:
        await ctx.send(f"{ctx.author.mention}, I couldn't DM you. Here's your reminder: **{reminder}**")

bot.run(TOKEN)
                              
