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
afk_users = {}

win_messages = ["🎉 Victory is yours!", "😎 You outplayed me!", "🔥 You crushed it!"]
loss_messages = ["😂 I win this time!", "🧠 Outsmarted you!", "😈 Better luck next time!"]

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
    # (unchanged logic)
    pass

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

# ✅ UPDATED RPS command: Member vs Member
@bot.command()
async def rps(ctx, opponent: discord.Member = None):
    if not opponent or opponent.bot or opponent == ctx.author:
        await ctx.send("❌ Please mention a valid member to challenge.")
        return

    emojis = {"🪨": "rock", "📄": "paper", "✂️": "scissors"}
    message = await ctx.send(
        f"🎮 Rock-Paper-Scissors Challenge!\n"
        f"{ctx.author.mention} vs {opponent.mention}\n"
        f"React with your choice below 👇"
    )

    for emoji in emojis.keys():
        await message.add_reaction(emoji)

    choices = {}

    def check(reaction, user):
        return (
            user in [ctx.author, opponent] and
            reaction.message.id == message.id and
            str(reaction.emoji) in emojis
        )

    while len(choices) < 2:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
            if user.id not in choices:
                choices[user.id] = emojis[str(reaction.emoji)]
        except asyncio.TimeoutError:
            await ctx.send("⏰ Game cancelled due to inactivity.")
            return

    p1_choice = choices[ctx.author.id]
    p2_choice = choices[opponent.id]

    result = ""
    if p1_choice == p2_choice:
        result = "🤝 It's a tie!"
    elif (p1_choice == "rock" and p2_choice == "scissors") or \
         (p1_choice == "paper" and p2_choice == "rock") or \
         (p1_choice == "scissors" and p2_choice == "paper"):
        result = f"🎉 {ctx.author.mention} wins!"
    else:
        result = f"🎉 {opponent.mention} wins!"

    emoji_lookup = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
    await ctx.send(
        f"{ctx.author.mention} chose {emoji_lookup[p1_choice]} **{p1_choice.capitalize()}**\n"
        f"{opponent.mention} chose {emoji_lookup[p2_choice]} **{p2_choice.capitalize()}**\n\n"
        f"**{result}**"
    )

@bot.command(name="info")
async def info_command(ctx):
    embed = discord.Embed(title="📖 Member Commands", color=discord.Color.purple())

    embed.add_field(
        name="👥 Fun & Utility",
        value="`$ship @user1 @user2` - Ship two users\n"
              "`$choose option1, option2` - Randomly choose one\n"
              "`$avatar [@user]` - Get user's avatar\n"
              "`$8b question` - Magic 8-Ball answers\n"
              "`$remind [seconds] [task]` - Set a reminder\n"
              "`$afk [reason]` - Set your AFK\n"
              "`$rps @user` - Challenge someone to Rock-Paper-Scissors\n",
        inline=False
    )

    embed.set_footer(text="Use the commands with $ prefix.")
    await ctx.send(embed=embed)

# (Other commands like createembed, role, support, etc. remain unchanged)

keep_alive()
bot.run(TOKEN)
