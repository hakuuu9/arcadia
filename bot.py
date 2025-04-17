import discord
from discord.ext import commands
from discord.ext.commands import Context
from config import TOKEN, GUILD_ID, ROLE_ID, VANITY_LINK
import random
import asyncio
import re
from flask import Flask
from threading import Thread

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="$", intents=intents)

afk_users = {}

# Flask keep-alive server for Render
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_flask).start()

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
    choices = [opt.strip() for opt in options.split(",") if opt.strip()]
    if len(choices) < 2:
        await ctx.send("Please provide at least two choices, separated by commas.")
        return
    selected = random.choice(choices)
    await ctx.send(f"🎲 I choose: **{selected}**")

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    guild = after.guild
    role = guild.get_role(ROLE_ID)

    if not role:
        return

    if hasattr(before, "bio") and hasattr(after, "bio") and before.bio != after.bio:
        before_bio = before.bio or ""
        after_bio = after.bio or ""

        has_vanity_before = VANITY_LINK in before_bio
        has_vanity_after = VANITY_LINK in after_bio

        if has_vanity_after and not has_vanity_before:
            if role not in after.roles:
                await after.add_roles(role)
                print(f"Gave {after} the role for adding vanity link.")

        elif has_vanity_before and not has_vanity_after:
            if role in after.roles:
                await after.remove_roles(role)
                print(f"Removed role from {after} for removing vanity link.")

bot.run(TOKEN)
