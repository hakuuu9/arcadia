import discord
from discord.ext import commands, tasks
import random
import asyncio
from config import TOKEN, GUILD_ID, ROLE_ID, VANITY_LINK, LOG_CHANNEL_ID
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix="$", intents=intents)

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
                    await channel.send(f"Added role to {member.mention} for having vanity link in status.")
        else:
            if ROLE_ID in [role.id for role in member.roles]:
                await member.remove_roles(discord.Object(id=ROLE_ID))
                channel = bot.get_channel(LOG_CHANNEL_ID)
                if channel:
                    await channel.send(f"Removed role from {member.mention} for removing vanity link from status.")
    except Exception as e:
        print(f"Error in presence_update: {e}")

@bot.command()
async def avatar(ctx, user: discord.User = None):
    user = user or ctx.author
    await ctx.send(user.display_avatar.url)

@bot.command()
async def ship(ctx, user1: discord.Member, user2: discord.Member):
    percent = random.randint(0, 100)
    message = f"**{user1.display_name}** + **{user2.display_name}** = **{percent}%**"
    if percent >= 50:
        nicknames = ["Sweethearts", "Power Couple", "Tortolitos", "Lovebirds"]
        nickname = random.choice(nicknames)
        message += f"\nThey are definitely **{nickname}**!"
    await ctx.send(message)

@bot.command()
async def eightball(ctx, *, question):
    responses = [
        "Yes", "No", "Maybe", "Definitely", "Absolutely not", "Ask again later",
        "Without a doubt", "Don't count on it", "Signs point to yes", "Very doubtful"
    ]
    await ctx.send(f"Question: {question}\nAnswer: {random.choice(responses)}")

@bot.command()
async def remind(ctx, time: int, *, task: str):
    await ctx.send(f"Reminder set for {time} seconds from now: **{task}**")
    await asyncio.sleep(time)
    await ctx.send(f"{ctx.author.mention}, reminder: **{task}**")

keep_alive()
bot.run(TOKEN)
        
