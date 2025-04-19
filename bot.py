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
                        f"• sticker and emoji perms\n"
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
async def info(ctx):
    embed = discord.Embed(title="Command Help", description="Here is a list of commands you can use:", color=discord.Color.blue())
    embed.add_field(name="$ship [user1] [user2]", value="Ships two users and gives a compatibility percentage.", inline=False)
    embed.add_field(name="$choose [option1, option2, ...]", value="Lets you choose randomly between the options.", inline=False)
    embed.add_field(name="$afk [reason]", value="Set yourself as AFK, mention the reason (default: AFK).", inline=False)
    embed.add_field(name="$avatar [user]", value="Shows the avatar of the user. If no user is provided, shows your avatar.", inline=False)
    embed.add_field(name="$8b [question]", value="Ask the magic 8-ball a question and get a random answer.", inline=False)
    embed.add_field(name="$remind [time in seconds] [task]", value="Sets a reminder for the task after the specified time.", inline=False)
    embed.add_field(name="$info", value="Shows this help message.", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def createembed(ctx, *, content: str):
    try:
        # Split content into title and body
        title, body = content.split(" | ", 1) if " | " in content else (None, content)

        # Create embed
        embed = discord.Embed(description=body, color=discord.Color.random())
        
        # Add title if exists
        if title:
            embed.title = title
        
        # Send embed
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"An error occurred while creating the embed: {e}")

keep_alive()
bot.run(TOKEN)
