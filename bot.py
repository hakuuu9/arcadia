import discord
from discord.ext import commands
from config import BOT_TOKEN, ROLE_ID, INVITE_LINK, LOG_CHANNEL_ID
from keep_alive import keep_alive
import os

# AFK users storage
afk_users = {}

# Intents
intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="+", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user.name} is online!")

# +afk command
@bot.command()
async def afk(ctx, *, message: str = "I'm currently AFK."):
    afk_users[ctx.author.id] = message
    await ctx.reply(f"✅ {ctx.author.display_name} is now AFK: `{message}`", mention_author=False)

# +avatar command
@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    avatar_url = member.display_avatar.url

    embed = discord.Embed(
        title=f"{member.display_name}'s Avatar",
        color=discord.Color.blue()
    )
    embed.set_image(url=avatar_url)
    await ctx.send(embed=embed)

# Detect if user returns from AFK or tags someone AFK
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id in afk_users:
        del afk_users[message.author.id]
        await message.channel.send(f"👋 Welcome back, {message.author.mention}! Your AFK status has been removed.")

    for user in message.mentions:
        if user.id in afk_users:
            await message.channel.send(f"💤 {user.display_name} is AFK: {afk_users[user.id]}")

    await bot.process_commands(message)

# Presence and bio check
@bot.event
async def on_presence_update(before, after):
    member = after
    if member.bot:
        return

    # Check custom status
    custom_status = next(
        (activity for activity in member.activities if activity.type == discord.ActivityType.custom),
        None
    )
    custom_state = custom_status.state if custom_status else ""

    # Try to get bio
    try:
        full_user = await bot.fetch_user(member.id)
        bio = getattr(full_user, "bio", "") or ""
    except Exception as e:
        print(f"Error fetching bio in presence_update: {e}")
        bio = ""

    link_in_status = INVITE_LINK in (custom_state or "")
    link_in_bio = INVITE_LINK in bio

    has_role = discord.utils.get(member.roles, id=ROLE_ID)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    if link_in_status or link_in_bio:
        if not has_role:
            try:
                await member.add_roles(discord.Object(id=ROLE_ID))
                print(f"✅ Added role to {member.display_name}")
                if log_channel:
                    await log_channel.send(f"✅ Added role to `{member.display_name}` (used vanity link).")
            except Exception as e:
                print(f"Error adding role: {e}")
    else:
        if has_role:
            try:
                await member.remove_roles(discord.Object(id=ROLE_ID))
                print(f"❌ Removed role from {member.display_name}")
                if log_channel:
                    await log_channel.send(f"❌ Removed role from `{member.display_name}` (removed vanity link).")
            except Exception as e:
                print(f"Error removing role: {e}")

# Keep alive for uptime services
keep_alive()

# Run bot
bot.run(BOT_TOKEN)
