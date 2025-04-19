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
    # (Unchanged from previous version...)
    pass

@bot.command()
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.send(f"🛑 {ctx.author.display_name} is now AFK: {reason}")

@bot.event
async def on_message(message):
    # (Unchanged from previous version...)
    await bot.process_commands(message)

# ✅ NEW RPS Command
@bot.command()
async def rps(ctx, user_choice: str):
    choices = ['rock', 'paper', 'scissors']
    bot_choice = random.choice(choices)
    user_choice = user_choice.lower()

    if user_choice not in choices:
        await ctx.send("❌ Invalid choice. Please choose rock, paper, or scissors.")
        return

    emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}

    if user_choice == bot_choice:
        result = "🤝 It's a tie!"
    elif (user_choice == "rock" and bot_choice == "scissors") or \
         (user_choice == "paper" and bot_choice == "rock") or \
         (user_choice == "scissors" and bot_choice == "paper"):
        result = f"🎉 You win! {random.choice(win_messages)}"
    else:
        result = f"😢 I win! {random.choice(loss_messages)}"

    await ctx.send(
        f"{emojis[user_choice]} You chose **{user_choice.capitalize()}**.\n"
        f"{emojis[bot_choice]} I chose **{bot_choice.capitalize()}**.\n"
        f"**{result}**"
    )

# (Other commands remain unchanged...)

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
              "`$rps [rock|paper|scissors]` - Rock Paper Scissors vs the bot\n",
        inline=False
    )

    embed.set_footer(text="Use the commands with $ prefix.")
    await ctx.send(embed=embed)

# (Support command, embed command, role command, etc. unchanged...)

keep_alive()
bot.run(TOKEN)
