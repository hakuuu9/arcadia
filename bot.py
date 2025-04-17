import discord
from discord.ext import commands
from config import BOT_TOKEN, ROLE_ID, INVITE_LINK, LOG_CHANNEL_ID
from keep_alive import keep_alive
import random

afk_users = {}

def generate_nickname(name1: str, name2: str) -> str:
    part1 = name1[: len(name1) // 2]
    part2 = name2[len(name2) // 2 :]
    return (part1 + part2).capitalize()

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="$", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user.name} is online and ready!")

# AFK command
@bot.command()
async def afk(ctx, *, message: str = "I'm currently AFK."):
    afk_users[ctx.author.id] = message
    await ctx.reply(f"✅ {ctx.author.display_name} is now AFK: `{message}`", mention_author=False)

# Avatar command
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

# Ship command
@bot.command()
async def ship(ctx, user1: discord.Member = None, user2: discord.Member = None):
    if not user1 or not user2:
        return await ctx.send("❗ Usage: `-ship @user1 @user2`")

    percentage = random.randint(0, 100)
    bar = "💖" * (percentage // 10) + "💔" * (10 - percentage // 10)
    description = (
        f"**{user1.display_name}** 💞 **{user2.display_name}**\n"
        f"Compatibility: **{percentage}%**\n{bar}"
    )
    if percentage >= 50:
        nickname = generate_nickname(user1.display_name, user2.display_name)
        description += f"\n\n💍 **Ship Name:** `{nickname}`"

    embed = discord.Embed(
        title="💘 Shipping Results 💘",
        description=description,
        color=discord.Color.magenta()
    )
    await ctx.send(embed=embed)

# 8ball command
@bot.command(name="8b")
async def eight_ball(ctx, *, question: str = None):
    if not question:
        await ctx.send("🎱 Please ask a yes/no question. Usage: `-8b Will I be lucky today?`")
        return

    responses = [
        "Yes, definitely.",
        "Without a doubt.",
        "Most likely.",
        "Ask again later.",
        "Cannot predict now.",
        "Don't count on it.",
        "My reply is no.",
        "Very doubtful."
    ]

    answer = random.choice(responses)
    await ctx.send(f"🎱 Question: `{question}`\nAnswer: **{answer}**")

# Message handler for AFK
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

# Role management based on status and bio
@bot.event
async def on_presence_update(before, after):
    member = after
    if member.bot:
        return

    custom_status = next(
        (act for act in member.activities if act.type == discord.ActivityType.custom),
        None
    )
    custom_state = custom_status.state if custom_status else ""

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

    if link_in_status or link_in_bio:
        if not has_role:
            try:
                await member.add_roles(discord.Object(id=ROLE_ID))
                print(f"✅ Added role to {member.display_name}")
                if log_channel:
                    await log_channel.send(
                        f"✅ Added role to `{member.display_name}` (vanity link detected)."
                    )
            except Exception as e:
                print(f"Error adding role: {e}")
    else:
        if has_role:
            try:
                await member.remove_roles(discord.Object(id=ROLE_ID))
                print(f"❌ Removed role from {member.display_name}")
                if log_channel:
                    await log_channel.send(
                        f"❌ Removed role from `{member.display_name}` (vanity link removed)."
                    )
            except Exception as e:
                print(f"Error removing role: {e}")

keep_alive()
bot.run(BOT_TOKEN)
        
