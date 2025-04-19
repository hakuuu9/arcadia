import discord
from discord.ext import commands, tasks
import random
import asyncio
import datetime
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

        if status and VANITY_LINK in status:
            if ROLE_ID not in [role.id for role in member.roles]:
                await member.add_roles(discord.Object(id=ROLE_ID))
                channel = bot.get_channel(LOG_CHANNEL_ID)
                if channel:
                    await channel.send(
                        f"```✅ Added role to {member.display_name} for having vanity link in status.\n\n"
                        f"Perks:\n"
                        f"• pic perms in ⁠💬・lounge\n"
                        f"• bypass giveaway with vanity role required```"
                    )
        else:
            if ROLE_ID in [role.id for role in member.roles]:
                await member.remove_roles(discord.Object(id=ROLE_ID))
                channel = bot.get_channel(LOG_CHANNEL_ID)
                if channel:
                    await channel.send(
                        f"```❌ Removed role from {member.display_name} for removing vanity link from status.```"
                    )
    except Exception as e:
        print(f"Error in presence_update: {e}")

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

    for user_id in afk_users:
        if f"<@{user_id}>" in message.content:
            reason = afk_users[user_id]
            await message.channel.send(f"💤 That user is AFK: {reason}")
            break

    await bot.process_commands(message)

@bot.command()
async def ship(ctx, user1: discord.Member, user2: discord.Member):
    percent = random.randint(0, 100)
    hearts = "❤️" * (percent // 20) or "💔"
    nicknames = ["Sweethearts", "Power Couple", "Tortolitos", "Lovebirds"]
    message = f"**{user1.display_name}** + **{user2.display_name}** = **{percent}%** {hearts}"
    if percent >= 50:
        nickname = random.choice(nicknames)
        message += f"\nThey are definitely **{nickname}**!"
    await ctx.send(message)

@bot.command()
async def choose(ctx, *, options: str):
    choices = [opt.strip() for opt in options.split(",") if opt.strip()]
    if len(choices) < 2:
        await ctx.send("Please provide at least two choices, separated by commas.")
        return
    selected = random.choice(choices)
    await ctx.send(f"🎲 I choose: **{selected}**")

@bot.command()
async def avatar(ctx, user: discord.User = None):
    user = user or ctx.author
    await ctx.send(user.display_avatar.url)

@bot.command(name="8b")
async def eightball(ctx, *, question):
    responses = [
        "Yes", "No", "Maybe", "Definitely", "Absolutely not", "Ask again later",
        "Without a doubt", "Don't count on it", "Signs point to yes", "Very doubtful"
    ]
    await ctx.send(f"🎱 Question: {question}\nAnswer: {random.choice(responses)}")

@bot.command()
async def remind(ctx, time: int, *, task: str):
    await ctx.send(f"⏰ Reminder set for {time} seconds from now: **{task}**")
    await asyncio.sleep(time)
    await ctx.send(f"🔔 {ctx.author.mention}, reminder: **{task}**")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def createembed(ctx, *, content: str):
    try:
        parts = [part.strip() for part in content.split("|")]
        if len(parts) < 3:
            await ctx.send("❌ Format: `$createembed #channel | [title] | [description] | [#hexcolor (optional)]`")
            return

        channel_mention = parts[0]
        title = parts[1] if parts[1].lower() != "none" else None
        description = parts[2]
        hex_color = parts[3] if len(parts) >= 4 else "#3498db"

        if not channel_mention.startswith("<#") or not channel_mention.endswith(">"):
            await ctx.send("❌ Please mention a valid channel.")
            return

        channel_id = int(channel_mention[2:-1])
        channel = bot.get_channel(channel_id)
        if not channel:
            await ctx.send("❌ Could not find that channel.")
            return

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.from_str(hex_color) if hex_color else discord.Color.blue()
        )
        embed.set_footer(text=f"Posted by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        await channel.send(embed=embed)
        await ctx.send(f"✅ Embed sent to {channel.mention}")

    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command(name="info")
async def info_command(ctx):
    embed = discord.Embed(title="📖 Member Command Info", color=discord.Color.purple())
    embed.add_field(
        name="👥 Member Commands",
        value="`$ship @user1 @user2` - Ship two users\n"
              "`$choose option1, option2` - Randomly choose one\n"
              "`$avatar [@user]` - Get user's avatar\n"
              "`$8b question` - Magic 8-Ball answers\n"
              "`$remind [seconds] [task]` - Set a reminder\n"
              "`$afk [reason]` - Set your AFK\n",
        inline=False
    )
    embed.set_footer(text="Use the commands with $ prefix.")
    await ctx.send(embed=embed)

@bot.command(name="support")
@commands.has_permissions(manage_messages=True)
async def support_command(ctx):
    embed = discord.Embed(title="🛠️ Staff Command Info", color=discord.Color.red())
    embed.add_field(
        name="📋 Staff Commands",
        value="`$createembed #channel | [title] | [description] | [#hexcolor (optional)]` - Post a custom embed",
        inline=False
    )
    embed.set_footer(text="These commands are for staff only.")
    await ctx.send(embed=embed)

keep_alive()
bot.run(TOKEN)
