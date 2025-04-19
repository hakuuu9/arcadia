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
async def ship(ctx, user1: discord.Member = None, user2: discord.Member = None):
    if not user1 or not user2:
        await ctx.send("Usage: `$ship @user1 @user2`")
        return
    percent = random.randint(0, 100)
    hearts = "❤️" * (percent // 20) or "💔"
    nicknames = ["Sweethearts", "Power Couple", "Tortolitos", "Lovebirds"]
    message = f"**{user1.display_name}** + **{user2.display_name}** = **{percent}%** {hearts}"
    if percent >= 50:
        nickname = random.choice(nicknames)
        message += f"\nThey are definitely **{nickname}**!"
    await ctx.send(message)

@bot.command()
async def choose(ctx, *, options: str = None):
    if not options:
        await ctx.send("Usage: `$choose option1, option2, option3`")
        return
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
async def eightball(ctx, *, question: str = None):
    if not question:
        await ctx.send("Usage: `$8b [your question]`")
        return
    responses = [
        "Yes", "No", "Maybe", "Definitely", "Absolutely not", "Ask again later",
        "Without a doubt", "Don't count on it", "Signs point to yes", "Very doubtful"
    ]
    await ctx.send(f"🎱 Question: {question}\nAnswer: {random.choice(responses)}")

@bot.command()
async def remind(ctx, time: int = None, *, task: str = None):
    if not time or not task:
        await ctx.send("Usage: `$remind [seconds] [task]`")
        return
    await ctx.send(f"⏰ Reminder set for {time} seconds from now: **{task}**")
    await asyncio.sleep(time)
    await ctx.send(f"🔔 {ctx.author.mention}, reminder: **{task}**")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def createembed(ctx, *, content: str = None):
    if not content:
        await ctx.send("Usage: `$createembed #channel | [title] | [description] | [hex color (optional)]`")
        return
    try:
        parts = [part.strip() for part in content.split("|")]
        if len(parts) < 2:
            await ctx.send("❌ Format: `$createembed #channel | [title] | [description] | [hex color (optional)]`")
            return

        channel_mention = parts[0]
        title = parts[1] if parts[1] else None
        description = parts[2] if len(parts) > 2 else None
        color_hex = parts[3] if len(parts) > 3 else None

        if not channel_mention.startswith("<#") or not channel_mention.endswith(">"):
            await ctx.send("❌ Please mention a valid channel.")
            return

        channel_id = int(channel_mention[2:-1])
        channel = bot.get_channel(channel_id)

        if not channel:
            await ctx.send("❌ Could not find that channel.")
            return

        color = discord.Color.blue()
        if color_hex:
            try:
                color = discord.Color(int(color_hex.strip("#"), 16))
            except:
                pass

        embed = discord.Embed(title=title if title else None, description=description, color=color)
        embed.set_footer(text=f"Posted by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        await channel.send(embed=embed)
        await ctx.send(f"✅ Embed sent to {channel.mention}")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member = None, *, role: discord.Role = None):
    if not member or not role:
        await ctx.send("Usage: `$role @member @role`")
        return

    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"⚠️ The {role.name} role has been formally rescinded from {member.mention}.")
    else:
        await member.add_roles(role)
        await ctx.send(f"🎖️ {member.mention} has been granted the {role.name} role.")

from discord import ui

@bot.command()
async def rps(ctx, opponent: discord.Member = None):
    if not opponent or opponent.bot or opponent == ctx.author:
        await ctx.send("❌ Please mention a valid member to challenge.")
        return

    class RPSView(ui.View):
        def __init__(self, challenger, opponent):
            super().__init__(timeout=60)
            self.challenger = challenger
            self.opponent = opponent
            self.choices = {}
            self.message = None

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user in [self.challenger, self.opponent]

        async def button_callback(self, interaction: discord.Interaction, choice: str):
            if interaction.user.id in self.choices:
                await interaction.response.send_message("❗ You've already made your choice.", ephemeral=True)
                return

            self.choices[interaction.user.id] = choice
            await interaction.response.send_message(f"✅ Choice locked in!", ephemeral=True)

            if len(self.choices) == 2:
                await self.show_result()

        async def show_result(self):
            p1_choice = self.choices[self.challenger.id]
            p2_choice = self.choices[self.opponent.id]

            emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
            result = ""
            if p1_choice == p2_choice:
                result = "🤝 It's a tie!"
            elif (p1_choice == "rock" and p2_choice == "scissors") or \
                 (p1_choice == "paper" and p2_choice == "rock") or \
                 (p1_choice == "scissors" and p2_choice == "paper"):
                result = f"🎉 {self.challenger.mention} wins!"
            else:
                result = f"🎉 {self.opponent.mention} wins!"

            await self.message.edit(content=(
                f"🪨 **Rock-Paper-Scissors Results!**\n"
                f"{self.challenger.mention} chose {emojis[p1_choice]} **{p1_choice.capitalize()}**\n"
                f"{self.opponent.mention} chose {emojis[p2_choice]} **{p2_choice.capitalize()}**\n"
                f"**{result}**"
            ), view=None)

        @ui.button(label="🪨 Rock", style=discord.ButtonStyle.primary)
        async def rock(self, interaction: discord.Interaction, button: ui.Button):
            await self.button_callback(interaction, "rock")

        @ui.button(label="📄 Paper", style=discord.ButtonStyle.primary)
        async def paper(self, interaction: discord.Interaction, button: ui.Button):
            await self.button_callback(interaction, "paper")

        @ui.button(label="✂️ Scissors", style=discord.ButtonStyle.primary)
        async def scissors(self, interaction: discord.Interaction, button: ui.Button):
            await self.button_callback(interaction, "scissors")

    view = RPSView(ctx.author, opponent)
    msg = await ctx.send(
        f"{ctx.author.mention} challenged {opponent.mention} to Rock-Paper-Scissors!\n"
        f"Both players, click a button to lock in your move.",
        view=view
    )
    view.message = msg

@bot.command(name="info")
async def info_command(ctx):
    embed = discord.Embed(title="📖 Bot Command Info", color=discord.Color.purple())

    embed.add_field(
        name="👥 Member Commands",
        value=(
            "`$ship @user1 @user2` - Ship two users\n"
            "`$choose option1, option2` - Randomly choose one\n"
            "`$avatar [@user]` - Get user's avatar\n"
            "`$8b question` - Magic 8-Ball answers\n"
            "`$remind [seconds] [task]` - Set a reminder\n"
            "`$afk [reason]` - Set your AFK\n"
            "`$rps @user` - Challenge a member to Rock-Paper-Scissors\n"
            "`$hangman solo` - Play Hangman by yourself\n"
            "`$hangman duo @user` - 2-player Hangman (take turns guessing)\n"
            "`$hangman free` - Free-for-all mode (everyone can guess)\n"
            "`$tictactoe @user` - Play Tic Tac Toe against someone\n"
        ),
        inline=False,
    )

    embed.set_footer(text="Use the commands with $ prefix.")
    await ctx.send(embed=embed)


@bot.command(name="supportinfo")
@commands.has_permissions(manage_messages=True)
async def support_info(ctx):
    embed = discord.Embed(
        title="🛠️ Support / Staff Commands",
        description="Only staff members can use these commands.",
        color=discord.Color.red()
    )

    embed.add_field(
        name="Support Commands",
        value=(
            "`$createembed #channel | [title] | [description] | [#hexcolor]` — Post a custom embed\n"
            "`$role @member @role` — Add or remove a role from a member"
        ),
        inline=False
    )

    embed.set_footer(text="Staff access only.")
    await ctx.send(embed=embed)


import aiohttp
@bot.command()
async def hangman(ctx, mode: str = "solo", opponent: discord.Member = None):
    # Fetch a random word from an online API
    async def fetch_word():
        async with aiohttp.ClientSession() as session:
            async with session.get("https://random-word-api.herokuapp.com/word") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data[0].lower()
                else:
                    return random.choice(["python", "discord", "hangman", "developer"])

    word = await fetch_word()
    display = ["_" for _ in word]
    guessed = set()
    attempts = 12
    turn = 0

    players = [ctx.author]
    if mode == "duo" and opponent and opponent != ctx.author and not opponent.bot:
        players.append(opponent)
    elif mode == "ffa":
        players = None  # anyone in the channel

    stages = [
        "```\n  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========```",
        "```\n  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========```",
        "```\n  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========```",
        "```\n  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========```",
        "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========```",
        "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========```",
        "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========```"
    ]

    def format_display():
        return " ".join(display)

    await ctx.send(
        f"🎯 **Hangman Game Started!** Mode: `{mode.upper()}`\n"
        f"Word: `{format_display()}`\nYou have {attempts} tries.\n{stages[0]}"
    )

    while attempts > 0 and "_" in display:
        if players:
            current_player = players[turn % len(players)]
            await ctx.send(f"🔁 {current_player.mention}, it's your turn to guess a letter.")

        try:
            guess_msg = await bot.wait_for(
                "message",
                timeout=60,
                check=lambda m: m.channel == ctx.channel and len(m.content) == 1 and m.content.isalpha() and (
                    players is None or m.author == current_player
                )
            )
        except asyncio.TimeoutError:
            await ctx.send("⏰ Time's up! Game cancelled.")
            return

        guess = guess_msg.content.lower()
        if guess in guessed:
            await ctx.send("⚠️ Letter already guessed.")
            continue

        guessed.add(guess)
        if guess in word:
            for i, c in enumerate(word):
                if c == guess:
                    display[i] = guess
            await ctx.send(f"✅ Correct! `{format_display()}`")
        else:
            attempts -= 1
            await ctx.send(f"❌ Wrong! `{format_display()}`\nTries left: {attempts}\n{stages[6 - attempts]}")

        if players:
            turn += 1

    if "_" not in display:
        await ctx.send(f"🎉 Congrats! The word was: `{word}`")
    else:
        await ctx.send(f"💀 Game Over! The word was `{word}`")

# Tic Tac Toe Setup
active_ttt_games = {}

@bot.command(name="tictactoe")
async def tictactoe(ctx, opponent: discord.Member):
    if ctx.author == opponent:
        return await ctx.send("❌ You can't play against yourself!")

    game_id = f"{ctx.channel.id}"
    if game_id in active_ttt_games:
        return await ctx.send("⚠️ A Tic Tac Toe game is already running in this channel.")

    board = [str(i) for i in range(1, 10)]
    players = [ctx.author, opponent]
    symbols = ["❌", "⭕"]
    current_turn = 0

    active_ttt_games[game_id] = {
        "board": board,
        "players": players,
        "symbols": symbols,
        "turn": current_turn
    }

    await ctx.send(render_board(board, players, symbols, current_turn))


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    game_id = f"{message.channel.id}"
    if game_id not in active_ttt_games:
        return await bot.process_commands(message)

    game = active_ttt_games[game_id]
    player = message.author
    if player != game["players"][game["turn"]]:
        return

    content = message.content.strip()
    if not content.isdigit() or not (1 <= int(content) <= 9):
        return await message.channel.send("⛔ Enter a number between 1 and 9.")

    pos = int(content) - 1
    if game["board"][pos] in ["❌", "⭕"]:
        return await message.channel.send("❗ That spot is already taken.")

    game["board"][pos] = game["symbols"][game["turn"]]

    if check_win(game["board"], game["symbols"][game["turn"]]):
        await message.channel.send(render_board(game["board"], game["players"], game["symbols"], game["turn"]))
        await message.channel.send(f"🏆 {player.mention} wins!")
        del active_ttt_games[game_id]
        return

    if all(cell in ["❌", "⭕"] for cell in game["board"]):
        await message.channel.send(render_board(game["board"], game["players"], game["symbols"], game["turn"]))
        await message.channel.send("🤝 It's a draw!")
        del active_ttt_games[game_id]
        return

    game["turn"] = 1 - game["turn"]
    await message.channel.send(render_board(game["board"], game["players"], game["symbols"], game["turn"]))

    await bot.process_commands(message)


def render_board(board, players, symbols, turn):
    b = board
    grid = f"```\n| {b[0]} | {b[1]} | {b[2]} |\n| {b[3]} | {b[4]} | {b[5]} |\n| {b[6]} | {b[7]} | {b[8]} |\n```"
    turn_msg = f"🎮 Tic Tac Toe: {players[0].mention} ({symbols[0]}) vs {players[1].mention} ({symbols[1]})\n\n" + grid
    turn_msg += f"\n{players[turn].mention}'s turn! Choose a number from 1–9."
    return turn_msg


def check_win(board, symbol):
    wins = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
        [0, 4, 8], [2, 4, 6]              # diagonals
    ]
    return any(all(board[i] == symbol for i in combo) for combo in wins)

keep_alive()
bot.run(TOKEN)
