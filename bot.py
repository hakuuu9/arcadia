import discord
from discord.ext import commands
import asyncio
import random
from config import TOKEN, GUILD_ID, ROLE_ID, VANITY_LINK, LOG_CHANNEL_ID

intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix="$", intents=intents)
afk_users = {}

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")

@bot.event
async def on_presence_update(before, after):
    try:
        guild = bot.get_guild(GUILD_ID)
        member = guild.get_member(after.id)
        if not member:
            return

        has_role = any(role.id == ROLE_ID for role in member.roles)
        custom_status = next((activity.state for activity in after.activities if activity.type == discord.ActivityType.custom), None)
        give_role = False

        if custom_status and VANITY_LINK in custom_status:
            give_role = True

        try:
            user_profile = await member.user.fetch_profile()
            if VANITY_LINK in user_profile.bio:
                give_role = True
        except Exception as e:
            print("Error fetching bio:", e)

        log_channel = bot.get_channel(LOG_CHANNEL_ID)

        if give_role and not has_role:
            await member.add_roles(discord.Object(id=ROLE_ID))
            if log_channel:
                await log_channel.send(f"✅ {member.mention} used the vanity link. Role added.")
        elif not give_role and has_role:
            await member.remove_roles(discord.Object(id=ROLE_ID))
            if log_channel:
                await log_channel.send(f"❌ {member.mention} removed the vanity link. Role removed.")

    except Exception as e:
        print("Error in presence update:", e)

@bot.command()
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.send(f"{ctx.author.mention} is now AFK: {reason}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id in afk_users:
        await message.channel.send(f"Welcome back {message.author.mention}, I removed your AFK status.")
        afk_users.pop(message.author.id)

    for user_id in afk_users:
        if f"<@{user_id}>" in message.content:
            reason = afk_users[user_id]
            user = message.guild.get_member(user_id)
            await message.channel.send(f"{user.display_name} is AFK: {reason}")
            break

    await bot.process_commands(message)

@bot.command()
async def avatar(ctx, user: discord.Member = None):
    user = user or ctx.author
    await ctx.send(f"{user.name}'s avatar: {user.display_avatar.url}")

@bot.command()
async def ship(ctx, user1: discord.Member, user2: discord.Member):
    percent = random.randint(1, 100)
    msg = f"**{user1.display_name}** ❤️ **{user2.display_name}**\nLove chance: **{percent}%**"
    if percent >= 50:
        nicknames = ["Sweethearts", "Power Couple", "Lovebirds", "Destiny Pair", "True Match"]
        msg += f"\nCouple nickname: **{random.choice(nicknames)}**"
    await ctx.send(msg)

@bot.command(aliases=["8ball"])
async def eightball(ctx, *, question):
    responses = [
        "Yes", "No", "Maybe", "Definitely", "I don't think so", "Absolutely",
        "Not sure", "Ask again later", "Certainly", "Never"
    ]
    await ctx.send(f"🎱 Question: {question}\nAnswer: {random.choice(responses)}")

@bot.command()
async def remind(ctx, time: str, *, reminder: str):
    unit = time[-1]
    try:
        value = int(time[:-1])
    except:
        await ctx.send("Invalid format! Use `10s`, `5m`, `1h`, or `1d`.")
        return

    multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    if unit not in multipliers:
        await ctx.send("Use time units like s, m, h, d.")
        return

    seconds = value * multipliers[unit]
    await ctx.send(f"⏰ Reminder set! I'll remind you in {time}.")

    await asyncio.sleep(seconds)
    try:
        await ctx.author.send(f"Reminder: **{reminder}**")
    except discord.Forbidden:
        await ctx.send(f"{ctx.author.mention}, I couldn't DM you. Here's your reminder: **{reminder}**")

bot.run(TOKEN)
            
