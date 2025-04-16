import discord
from discord.ext import commands
from config import BOT_TOKEN, ROLE_ID, INVITE_LINK, LOG_CHANNEL_ID
from keep_alive import keep_alive
import random

# AFK users storage
afk_users = {}

# Intents
intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="-", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user.name} is online and ready!")

# ——— AFK Command ———
@bot.command()
async def afk(ctx, *, message: str = "I'm currently AFK."):
    afk_users[ctx.author.id] = message
    await ctx.reply(f"✅ {ctx.author.display_name} is now AFK: `{message}`", mention_author=False)

# ——— Avatar Command ———
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

# ——— Ship Command ———
@bot.command()
async def ship(ctx, user1: discord.Member = None, user2: discord.Member = None):
    if not user1 or not user2:
        return await ctx.send("❗ Usage: `-ship @user1 @user2`")
    percentage = random.randint(0, 100)
    bar = "💖" * (percentage // 10) + "💔" * (10 - percentage // 10)
    embed = discord.Embed(
        title="💘 Shipping Results 💘",
        description=(
            f"**{user1.display_name}** 💞 **{user2.display_name}**\n"
            f"Compatibility: **{percentage}%**\n{bar}"
        ),
        color=discord.Color.magenta()
    )
    await ctx.send(embed=embed)

# ——— Message Handler (AFK & command processing) ———
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Remove AFK if the user speaks again
    if message.author.id in afk_users:
        del afk_users[message.author.id]
        await message.channel.send(f"👋 Welcome back, {message.author.mention}! Your AFK status has been removed.")

    # Notify when mentioning an AFK user
    for user in message.mentions:
        if user.id in afk_users:
            await message.channel.send(f"💤 {user.display_name} is AFK: {afk_users[user.id]}")

    # Let prefix commands (like -ship) run
    await bot.process_commands(message)

# ——— Presence & Bio Checker ———
@bot.event
async def on_presence_update(before, after):
    member = after
    if member.bot:
        return

    # Custom status
    custom_status = next(
        (act for act in member.activities if act.type == discord.ActivityType.custom),
        None
    )
    custom_state = custom_status.state if custom_status else ""

    # Fetch bio via HTTP (py-cord only)
    try:
        full_user = await bot.fetch_user(member.id)
        bio = getattr(full_user, "bio", "") or ""
    except Exception as e:
        print(f"Error fetching bio: {e}")
        bio = ""

    link_in_status = INVITE_LINK in (custom_state or "")
    link_in_bio = INVITE_LINK in bio

    has_role = discord.utils.get(member.roles, id=ROLE_ID)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    # Add role if link appears
    if link_in_status or link_in_bio:
        if not has_role:
            try:
                await member.add_roles(discord.Object(id=ROLE_ID))
                print(f"✅ Added role to {member.display_name}")
                if log_channel:
                    await log_channel.send(f"✅ Added role to `{member.display_name}` (vanity link detected).")
            except Exception as e:
                print(f"Error adding role: {e}")
    # Remove if link is gone from both status & bio
    else:
        if has_role:
            try:
                await member.remove_roles(discord.Object(id=ROLE_ID))
                print(f"❌ Removed role from {member.display_name}")
                if log_channel:
                    await log_channel.send(f"❌ Removed role from `{member.display_name}` (vanity link removed).")
            except Exception as e:
                print(f"Error removing role: {e}")

# Keep the webserver alive for UptimeRobot / Render
keep_alive()

# Run the bot
bot.run(BOT_TOKEN)
