import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import random
from openai import OpenAI
import math
import asyncio
import json
import re
import os
import html
import time
import datetime
import aiohttp
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from collections import defaultdict
from config import TOKEN, GUILD_ID, ROLE_ID, VANITY_LINK, LOG_CHANNEL_ID, VANITY_IMAGE_URL
from keep_alive import keep_alive
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix="$", intents=intents)


@bot.event
async def on_presence_update(before, after):
    member = after
    try:
        # Extract custom status
        status = None
        for activity in after.activities:
            if activity.type == discord.ActivityType.custom:
                status = activity.state
                break

        has_role = any(role.id == ROLE_ID for role in member.roles)

        # Role granting
        if status and VANITY_LINK in status and not has_role:
            await member.add_roles(discord.Object(id=ROLE_ID))

            embed = discord.Embed(
                title="Vanity Role Granted",
                description=(
                    f"The role **<@&{ROLE_ID}>** has been assigned to **{member.mention}** "
                    f"for including the official vanity link in their custom status.\n\n"
                    "**Privileges:**\n"
                    "• Nickname perms\n"
                    "• Image and embed link perms\n"
                    "• 1.0 XP boost\n"
                ),
                color=discord.Color.green()
            )
            embed.set_image(url=VANITY_IMAGE_URL)
            embed.set_footer(text=f"Status verified for {member.name}.")

            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(embed=embed)

        # Role removal
        elif (not status or VANITY_LINK not in status) and has_role:
            await member.remove_roles(discord.Object(id=ROLE_ID))

            embed = discord.Embed(
                title="Vanity Role Removed",
                description=(
                    f"The role **<@&{ROLE_ID}>** has been removed from **{member.mention}** "
                    f"as the vanity link is no longer present in their status."
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Status updated for {member.name}.")

            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(embed=embed)

    except Exception as e:
        print(f"[Error - Vanity Role Handler]: {e}")


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

import re

@bot.command()
async def remind(ctx, time: str = None, *, task: str = None):
    if not time or not task:
        await ctx.send(
            "Usage: `$remind [time][s/m/h] [task]`\n"
            "Examples: `$remind 10s take out the trash`, `$remind 5min start homework`, `$remind 1h30m read a book`"
        )
        return

    # Pattern to match multiple time parts like 1h30m20s
    time_pattern = re.findall(r"(\d+)(h|hr|hrs|m|min|mins|s|sec|secs)", time.lower())
    
    if not time_pattern:
        await ctx.send("❌ Invalid time format. Use combinations like `1h30m`, `10min30s`, or `2h`.")
        return

    delay = 0
    for value, unit in time_pattern:
        value = int(value)
        if unit in ["h", "hr", "hrs"]:
            delay += value * 3600
        elif unit in ["m", "min", "mins"]:
            delay += value * 60
        elif unit in ["s", "sec", "secs"]:
            delay += value
        else:
            await ctx.send("❌ Invalid time unit detected.")
            return

    if delay <= 0:
        await ctx.send("❌ Time must be greater than 0 seconds.")
        return

    await ctx.send(f"⏰ Reminder set for `{time}`: **{task}**")
    await asyncio.sleep(delay)
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

        # Get channel
        if not channel_mention.startswith("<#") or not channel_mention.endswith(">"):
            await ctx.send("❌ Please mention a valid channel.")
            return

        channel_id = int(channel_mention[2:-1])
        channel = bot.get_channel(channel_id)

        if not channel:
            await ctx.send("❌ Could not find that channel.")
            return

        # Parse color
        color = discord.Color.blue()
        if color_hex:
            try:
                color = discord.Color(int(color_hex.strip("#"), 16))
            except:
                pass

        # Build embed
        embed = discord.Embed(
            title=title if title else None,
            description=description,
            color=color
        )
        embed.set_footer(text=f"Posted by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        # Check for uploaded image
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if attachment.content_type and attachment.content_type.startswith("image/"):
                embed.set_image(url=attachment.url)

        await channel.send(embed=embed)
        await ctx.send(f"✅ Embed sent to {channel.mention}")

    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")



@bot.command()
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member = None, *, role_input: str = None):
    STAFF_ROLE_ID = 1347181345922748456  # 🔒 Replace with your actual staff role ID

    # Check if the author has the required staff role
    if STAFF_ROLE_ID not in [role.id for role in ctx.author.roles]:
        await ctx.send("❌ You don't have the required staff role to add or remove roles.")
        return

    if not member or not role_input:
        await ctx.send("Usage: `$role @member @role`")
        return

    role = None
    if role_input.isdigit():
        role = ctx.guild.get_role(int(role_input))
    elif role_input.startswith("<@&") and role_input.endswith(">"):
        role_id = int(role_input[3:-1])
        role = ctx.guild.get_role(role_id)
    else:
        role = discord.utils.find(lambda r: r.name.lower() == role_input.lower(), ctx.guild.roles)

    if not role:
        await ctx.send("❌ Couldn't find that role.")
        return

    embed = discord.Embed(color=discord.Color.blurple())
    embed.set_thumbnail(url="https://i.imgur.com/JxsCfCe.gif")
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

    if role in member.roles:
        await member.remove_roles(role)
        embed.title = "🔻 Role Removed"
        embed.description = f"{member.mention} is no longer **{role.name}**."
    else:
        await member.add_roles(role)
        embed.title = "🎖️ Role Granted"
        embed.description = f"{member.mention} has been promoted to **{role.name}**."

    await ctx.send(embed=embed)

    log_channel = ctx.guild.get_channel(1364839238960549908)  # Replace with your actual log channel ID
    if log_channel:
        await log_channel.send(embed=embed)



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

# ------------------------------------------------------------------------------------ start of bot info

@bot.command(name="info")
async def info_command(ctx):
    pages = [
        discord.Embed(
            title="📖 Arcadian Bot Command Info - Page 1",
            description="Explore all my features, games, utilities, and more!",
            color=discord.Color.purple()
        ).add_field(
            name="👥 Member Commands",
            value=(
                "🔹 `$ship @user1 @user2` - Ship two users\n"
                "🔹 `$choose option1, option2` - Randomly choose one\n"
                "🔹 `$avatar [@user]` - Get user's avatar\n"
                "🔹 `$8b question` - Magic 8-Ball answers\n"
                "🔹 `$remind [time] [task]` - Set a reminder\n"
                "🔹 `$afk [reason]` - Set your AFK status\n"
                "🔹 `$simpfor @user` – See how hard you're simping for someone\n"
                "🔹 `$userinfo [@user]` – Display user info\n"
                "🔹 `$message` – Count a user's messages (overall & per channel)"
                "🔹 `$autoresponse add/delete/list` – Set auto-replies for keywords\n"
                "🔹 `$quote` - Reply to a message and turn it into a styled quote image\n"
                "🔹 `$confess your message` - Send an anonymous confession to a set channel. Also logs the sender privately.\n"
                "🔹 `$snipe` – Retrieve the last deleted message in a channel\n"
            ),
            inline=False
        ).set_thumbnail(url="https://i.imgur.com/JxsCfCe.gif"),

        discord.Embed(
            title="🎮 Arcadian Bot Command Info - Page 2",
            description="Time to play!",
            color=discord.Color.purple()
        ).add_field(
            name="🎮 Game Commands",
            value=(
                "🎲 `$rps @user` - Rock-Paper-Scissors\n"
                "🎯 `$hangman solo` / `duo @user` / `free` - Hangman modes\n"
                "❌ `$tictactoe @user` - Play Tic Tac Toe\n"
                "🔤 `$wordchain [word]` - Continue the chain\n"
                "🧠 `$unscramble` – Word puzzle\n"
                "🏆 `$unscramblescore` – Leaderboard\n"
                "🤔 `$spotlie` - Find the lie!\n"
            ),
            inline=False
        ).set_thumbnail(url="https://i.imgur.com/JxsCfCe.gif"),

        discord.Embed(
            title="🛠️ Arcadian Bot Command Info - Page 3",
            description="Useful tools and utilities.",
            color=discord.Color.purple()
        ).add_field(
            name="🔧 Utility Commands",
            value=(
                "🤖 `$arcadia [question]` - Ask Arcadia anything"
            ),
            inline=False
        ).set_thumbnail(url="https://i.imgur.com/JxsCfCe.gif"),
    ]

    current_page = 0

    class PaginatorView(View):
        def __init__(self):
            super().__init__(timeout=300)
            self.value = None

        @discord.ui.button(label="◀️ Prev", style=discord.ButtonStyle.blurple)
        async def prev(self, interaction: discord.Interaction, button: Button):
            nonlocal current_page
            if interaction.user != ctx.author:
                await interaction.response.send_message("Only the command author can use the buttons!", ephemeral=True)
                return

            current_page = (current_page - 1) % len(pages)
            await interaction.response.edit_message(embed=pages[current_page], view=self)

        @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.blurple)
        async def next(self, interaction: discord.Interaction, button: Button):
            nonlocal current_page
            if interaction.user != ctx.author:
                await interaction.response.send_message("Only the command author can use the buttons!", ephemeral=True)
                return

            current_page = (current_page + 1) % len(pages)
            await interaction.response.edit_message(embed=pages[current_page], view=self)

        async def on_timeout(self):
            for child in self.children:
                child.disabled = True
            try:
                await message.edit(view=self)
            except:
                pass

    view = PaginatorView()
    message = await ctx.send(embed=pages[current_page], view=view)


@bot.command(name="supportinfo")
@commands.has_permissions(manage_messages=True)
async def support_info(ctx):
    embed = discord.Embed(
        title="🛠️ Arcadian Staff Commands",
        description="**These commands are for server staff and support team only.**",
        color=discord.Color.red()
    )

    embed.set_thumbnail(url="https://i.imgur.com/JxsCfCe.gif")  # Optional: same GIF for consistency

    embed.add_field(
        name="🧰 Moderation & Support Tools",
        value=(
            "📩 `$createembed #channel | title | description | #hexcolor` – Post a styled embed\n"
            "🎭 `$role @member @role` – Add/remove a role from a member\n"
            "📊 `$serverinfo` – Show server stats and info\n"
            "🧹 `$purge [amount]` – Delete messages in a channel\n"
            "⚠️ `$warn @user reason` – Warn a user & log it\n"
            "📌 `$inrole` – Show members with a certain role\n"
            "📊 `$arclb` – $arclb #channel | [title] | [description] | [hex color (optional)] | [GIF URL (optional)]\n"
            "📊 `$sticky #channel your message` - Set a sticky message that reposts when users chat.\n"
            "📊 `$unsticky #channel` - Remove a sticky message from a channel.\n"
            "👢 `$kick @user reason` – Kick a member from the server\n"
            "🔨 `$ban @user reason` – Ban a member from the server\n"
            "🔇 `$timeout @user seconds reason` – Timeout (mute) a user temporarily\n"
        ),
        inline=False
    )

    embed.set_footer(text="Only users with Manage Messages permission can use these.")
    await ctx.send(embed=embed)

# -------------------------------------------------------------------------------- end of bot info

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

wordchain_sessions = {}

@bot.command()
async def wordchain(ctx, start_word: str):
    channel_id = ctx.channel.id
    if channel_id in wordchain_sessions:
        return await ctx.send("⚠️ A Word Chain game is already running in this channel!")

    game_data = {
        "used_words": [start_word.lower()],
        "last_letter": start_word[-1].lower(),
        "channel": ctx.channel,
        "active": True
    }
    wordchain_sessions[channel_id] = game_data

    await ctx.send(
        f"🧠 **Word Chain Game Started!**\n"
        f"First word: **{start_word}**\n"
        f"Next word must start with **'{game_data['last_letter']}'**. Type your word in chat!"
    )

    while game_data["active"]:
        try:
            msg = await bot.wait_for(
                "message",
                check=lambda m: m.channel == ctx.channel and not m.author.bot,
                timeout=30.0
            )
            word = msg.content.strip().lower()

            if word in game_data["used_words"]:
                await ctx.send(f"🚫 That word’s already been used, {msg.author.mention}!")
                continue

            if word[0] != game_data["last_letter"]:
                await ctx.send(f"❌ Your word must start with **'{game_data['last_letter']}'**, {msg.author.mention}!")
                continue

            game_data["used_words"].append(word)
            game_data["last_letter"] = word[-1]
            await ctx.send(f"✅ **{word}** accepted! Next word must start with **'{game_data['last_letter']}'**.")

        except asyncio.TimeoutError:
            await ctx.send("⏰ No response in 30 seconds. Game over!")
            del wordchain_sessions[channel_id]
            break

@bot.command()
async def stopwordchain(ctx):
    channel_id = ctx.channel.id
    if channel_id in wordchain_sessions:
        del wordchain_sessions[channel_id]
        await ctx.send("🛑 Word Chain game ended.")
    else:
        await ctx.send("❌ There’s no active Word Chain game in this channel.")

class GuessButton(Button):
    def __init__(self, number, correct_number):
        super().__init__(label=str(number), style=discord.ButtonStyle.primary)
        self.number = number
        self.correct_number = correct_number
        self.clicked_users = set()

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        if user_id in self.clicked_users:
            await interaction.response.send_message("🕒 You're on cooldown! Try again in 2 seconds.", ephemeral=True)
            return

        self.clicked_users.add(user_id)
        await asyncio.sleep(2)
        self.clicked_users.remove(user_id)

        if self.number == self.correct_number:
            for child in self.view.children:
                child.disabled = True
                if isinstance(child, GuessButton) and child.number == self.correct_number:
                    child.style = discord.ButtonStyle.success
            await interaction.response.edit_message(content=f"🎉 {interaction.user.mention} guessed the correct number **{self.correct_number}**!", view=self.view)
        else:
            await interaction.response.send_message("❌ Nope, try again!", ephemeral=True)


@bot.command()
async def unscramble(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://random-word-api.herokuapp.com/word?number=1") as resp:
            if resp.status != 200:
                return await ctx.send("❌ Failed to fetch a word. Try again later.")
            data = await resp.json()
            word = data[0]

    scrambled = ''.join(random.sample(word, len(word)))
    await ctx.send(f"🧩 Unscramble this word: **{scrambled}** (60s to answer!)")

    def check(m):
        return m.channel == ctx.channel and m.content.lower() == word.lower()

    try:
        msg = await bot.wait_for("message", check=check, timeout=60.0)
        author_id = msg.author.id
        unscramble_scores[author_id] = unscramble_scores.get(author_id, 0) + 1

        # Save scores to file
        with open(SCORE_FILE, "w") as f:
            json.dump(unscramble_scores, f, indent=2)

        await ctx.send(f"✅ Correct! {msg.author.mention} got it: **{word}** (+1 point!)")
    except asyncio.TimeoutError:
        await ctx.send(f"⏱️ Time's up! The word was **{word}**.")

@bot.command()
async def unscramblescore(ctx):
    if not unscramble_scores:
        return await ctx.send("📉 No scores yet. Be the first to play!")

    sorted_scores = sorted(unscramble_scores.items(), key=lambda x: x[1], reverse=True)
    lines = []
    for user_id, score in sorted_scores[:10]:
        user = await bot.fetch_user(user_id)
        lines.append(f"**{user.name}** — {score} points")

    embed = discord.Embed(title="🏆 Unscramble Leaderboard", description="\n".join(lines), color=0x00ff99)
    await ctx.send(embed=embed)

@bot.command(name="spotlie")
async def spotlie(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://opentdb.com/api.php?amount=3&type=boolean") as resp:
            if resp.status != 200:
                return await ctx.send("❌ Couldn't fetch facts. Try again later.")
            data = await resp.json()

    questions = data.get("results", [])
    if len(questions) < 3:
        return await ctx.send("❌ Not enough data received from the API.")

    # Extract statements and their truth values
    statements = [html.unescape(q["question"]) for q in questions]
    truths = [q["correct_answer"] == "True" for q in questions]

    # Ensure at least two truths and one lie
    if truths.count(True) < 2:
        # Flip one false to true
        for i in range(len(truths)):
            if not truths[i]:
                truths[i] = True
                break
    if truths.count(False) < 1:
        # Flip one true to false
        for i in range(len(truths)):
            if truths[i]:
                truths[i] = False
                break

    # Shuffle the statements
    combined = list(zip(statements, truths))
    random.shuffle(combined)
    statements, truths = zip(*combined)

    embed = discord.Embed(
        title="**Spot the Lie!**",
        description="\n".join([f"{i+1}. {stmt}" for i, stmt in enumerate(statements)]),
        color=discord.Color.orange()
    )
    embed.set_footer(text="Type 1, 2, or 3 to guess. You have 20 seconds!")

    await ctx.send(embed=embed)

    def check(m):
        return (
            m.channel == ctx.channel and
            m.content in ["1", "2", "3"]
        )

    guesses = {}
    try:
        while True:
            guess_msg = await bot.wait_for("message", timeout=20.0, check=check)
            user = guess_msg.author
            guess = int(guess_msg.content) - 1
            guesses[user.id] = guess
    except asyncio.TimeoutError:
        pass

    # Identify the lie
    lie_index = truths.index(False)
    correct_users = [user_id for user_id, guess in guesses.items() if guess == lie_index]
    user_mentions = [f"<@{uid}>" for uid in correct_users]

    result_embed = discord.Embed(
        title="Results",
        description=(
            f"The lie was: **{lie_index + 1}. {statements[lie_index]}**\n\n"
            f"{len(correct_users)} got it right!"
            + ("\n" + ", ".join(user_mentions) if user_mentions else "\nNo one guessed correctly!")
        ),
        color=discord.Color.green()
    )
    await ctx.send(embed=result_embed)

@bot.command(name="simpfor")
async def simpfor(ctx, member: discord.Member):
    if member.id == ctx.author.id:
        return await ctx.send("💀 You can't simp for yourself... or can you?")

    percent = random.randint(0, 100)

    if percent >= 90:
        level = "🫡 Down BAD. No recovery."
    elif percent >= 70:
        level = "💖 You’re simping hard!"
    elif percent >= 50:
        level = "😳 You got a little crush, huh?"
    elif percent >= 30:
        level = "🙂 Just a little admiration."
    elif percent >= 10:
        level = "😌 Meh. They're alright."
    else:
        level = "🚫 You're immune to the simp flu."

    embed = discord.Embed(
        title="💘 Simp Meter Activated",
        description=f"**{ctx.author.mention}** is **{percent}%** simping for **{member.mention}**.\n\n{level}",
        color=discord.Color.pink()
    )
    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title=f"📊 Server Info - {guild.name}",
        description="Here are some details about this server:",
        color=discord.Color.green()
    )

    embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
    embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
    embed.add_field(name="📅 Created On", value=guild.created_at.strftime("%Y-%m-%d %H:%M"), inline=False)
    embed.add_field(name="🆔 Server ID", value=guild.id, inline=True)
    embed.add_field(name="🌍 Region", value=str(guild.preferred_locale).replace('_', '-'), inline=True)

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    if amount <= 0:
        return await ctx.send("❌ Please provide a number greater than 0.")

    deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the purge command itself
    await ctx.send(f"🧹 Deleted {len(deleted)-1} messages!", delete_after=3)

@purge.error
async def purge_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Please specify the number of messages to delete. Example: `$purge 10`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("⚠️ That doesn't seem like a valid number. Please try again.")
    else:
        await ctx.send(f"⚠️ An error occurred: {error}")


MODLOG_CHANNEL_ID = 1350497918574006282  # Replace with your mod log channel ID
TALK_CHANNEL_ID = 1363918605678411807  # Channel where warned users are mentioned
WARNED_ROLE_ID = 1363911975016333402    # "Warned" role that lets users see the warning channel

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason: str = "No reason provided."):
    warning_message = (
        f"⚠️ You have been warned in **{ctx.guild.name}**.\n"
        f"**Reason:** {reason}"
    )

    # DM the user
    try:
        await member.send(warning_message)
    except discord.Forbidden:
        await ctx.send(f"❌ Couldn't DM {member.mention}, they may have DMs disabled.")

    # Add the warned role
    warned_role = ctx.guild.get_role(WARNED_ROLE_ID)
    if warned_role:
        await member.add_roles(warned_role)

    # Mention them in the confession/talk channel
    talk_channel = bot.get_channel(TALK_CHANNEL_ID)
    if talk_channel:
        await talk_channel.send(f"<@&{WARNED_ROLE_ID}> {member.mention}\n{warning_message}")

    # Confirmation in the current channel
    await ctx.send(f"✅ {member.mention} has been warned.")

    # Optional: log to mod channel
    log_channel = bot.get_channel(MODLOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(
            title="🚨 Member Warned",
            color=discord.Color.orange(),
            timestamp=ctx.message.created_at
        )
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Server: {ctx.guild.name}")
        await log_channel.send(embed=embed)




@bot.command(name="userinfo")
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author  # Use the command invoker if no member is mentioned
    roles = [role.mention for role in member.roles if role != ctx.guild.default_role]
    joined_at = member.joined_at.strftime("%Y-%m-%d %H:%M")
    created_at = member.created_at.strftime("%Y-%m-%d %H:%M")

    embed = discord.Embed(
        title=f"ℹ️ User Info - {member.display_name}",
        color=discord.Color.blurple()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="🆔 ID", value=member.id, inline=True)
    embed.add_field(name="👤 Username", value=str(member), inline=True)
    embed.add_field(name="📅 Joined Server", value=joined_at, inline=False)
    embed.add_field(name="🗓️ Account Created", value=created_at, inline=False)
    embed.add_field(name="🎭 Roles", value=", ".join(roles) if roles else "None", inline=False)
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

    await ctx.send(embed=embed)
# -----------------------------------------------------------------------------

afk_users = {}  # {user_id: {"reason": str, "since": datetime}}

@bot.command()
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = {
        "reason": reason,
        "since": datetime.datetime.utcnow()
    }
    await ctx.send(f"{ctx.author.mention} is now AFK: **{reason}**")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # If user was AFK and they spoke, remove their AFK
    if message.author.id in afk_users:
        del afk_users[message.author.id]
        await message.channel.send(f"👋 Welcome back, {message.author.mention}! Removed your AFK status.")

    # If someone mentions an AFK user
    for mention in message.mentions:
        if mention.id in afk_users:
            afk_info = afk_users[mention.id]
            since = afk_info["since"]
            delta = datetime.datetime.utcnow() - since
            minutes = int(delta.total_seconds() // 60)
            reason = afk_info["reason"]
            await message.channel.send(
                f"💤 {mention.display_name} is AFK ({minutes} min ago): **{reason}**"
            )

    await bot.process_commands(message)


# --------------------------------------------------------------------------------------

@bot.command()
async def inrole(ctx, *, role_input: str):
    # Case-insensitive role lookup
    role = None
    if role_input.startswith("<@&") and role_input.endswith(">"):
        role_id = int(role_input[3:-1])
        role = ctx.guild.get_role(role_id)
    elif role_input.isdigit():
        role = ctx.guild.get_role(int(role_input))
    else:
        role = discord.utils.find(lambda r: r.name.lower() == role_input.lower(), ctx.guild.roles)

    if not role:
        await ctx.send("❌ Role not found.")
        return

    members_with_role = [f"{i+1}. {member.mention}" for i, member in enumerate(role.members)]

    if not members_with_role:
        await ctx.send(f"No members currently have the role **{role.name}**.")
        return

    pages = [members_with_role[i:i + 10] for i in range(0, len(members_with_role), 10)]
    total_pages = len(pages)

    def create_embed(page_index):
        embed = discord.Embed(
            title=f"Members in Role: {role.name}",
            description="\n".join(pages[page_index]),
            color=discord.Color.blurple()
        )
        if role.icon:
            embed.set_thumbnail(url=role.icon.url)
        else:
            embed.set_thumbnail(url="https://i.imgur.com/JxsCfCe.gif")  # fallback gif

        embed.set_footer(text=f"Page {page_index + 1} of {total_pages} • Total members: {len(members_with_role)}")
        return embed

    class PaginationView(View):
        def __init__(self):
            super().__init__(timeout=300)
            self.page = 0

        @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
        async def previous(self, interaction: discord.Interaction, button: Button):
            if interaction.user != ctx.author:
                await interaction.response.send_message("Only the command user can use this.", ephemeral=True)
                return
            self.page = (self.page - 1) % total_pages
            await interaction.response.edit_message(embed=create_embed(self.page), view=self)

        @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
        async def next(self, interaction: discord.Interaction, button: Button):
            if interaction.user != ctx.author:
                await interaction.response.send_message("Only the command user can use this.", ephemeral=True)
                return
            self.page = (self.page + 1) % total_pages
            await interaction.response.edit_message(embed=create_embed(self.page), view=self)

    await ctx.send(embed=create_embed(0), view=PaginationView())


# Your OpenRouter API key and base URL
OPENROUTER_API_KEY = "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"
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Fancy embed GIF (replace with any hosted GIF URL)
HEADER_GIF_URL = "https://i.imgur.com/JxsCfCe.gif"

@bot.command()
async def arcadia(ctx, *, question: str):
    """Ask AI a question using OpenRouter."""

    thinking = await ctx.send("**Thinking...**")

    try:
        response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",  # You can change to any available OpenRouter model
            messages=[{"role": "user", "content": question}]
        )

        answer = response.choices[0].message.content.strip()

        embed = discord.Embed(
            title="Arcadia Assistant",
            description=answer,
            color=discord.Color.blurple()
        )
        embed.set_image(url=HEADER_GIF_URL)
        embed.set_footer(text=f"Question by {ctx.author.name}")

        await thinking.delete()
        await ctx.send(embed=embed)

    except Exception as e:
        await thinking.edit(content=f"**Something went wrong:** `{e}`")

@bot.command(name="arclb")
@commands.has_permissions(manage_messages=True)
async def arclb(ctx, *, content: str = None):
    if not content:
        await ctx.send("Usage: `$arclb #channel | [title] | [description] | [hex color (optional)] | [GIF URL (optional)]`")
        return
    try:
        parts = [part.strip() for part in content.split("|")]
        if len(parts) < 2:
            await ctx.send("❌ Format: `$arclb #channel | [title] | [description] | [hex color (optional)] | [GIF URL (optional)]`")
            return

        channel_mention = parts[0]
        title = parts[1] if parts[1] else None
        description = parts[2] if len(parts) > 2 else None
        color_hex = parts[3] if len(parts) > 3 else None
        gif_url = parts[4] if len(parts) > 4 else None

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

        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        embed.set_footer(text=f"Posted by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        # Optional thumbnail (GIF)
        if gif_url and (gif_url.endswith(".gif") or gif_url.endswith(".webp")):
            embed.set_thumbnail(url=gif_url)

        # Optional image attachment
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if attachment.content_type and attachment.content_type.startswith("image/"):
                embed.set_image(url=attachment.url)

        await channel.send(embed=embed)
        await ctx.send(f"✅ Embed sent to {channel.mention}")

    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

# ------------------------------------------------------------------------

message_counts = {}

# Load message count data from file
if os.path.exists("message_counts.json"):
    with open("message_counts.json", "r") as f:
        try:
            message_counts = json.load(f)
        except json.JSONDecodeError:
            message_counts = {}

# Event to track messages
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    channel_id = str(message.channel.id)

    if user_id not in message_counts:
        message_counts[user_id] = {"total": 0, "channels": {}}

    message_counts[user_id]["total"] += 1
    message_counts[user_id]["channels"][channel_id] = message_counts[user_id]["channels"].get(channel_id, 0) + 1

    await bot.process_commands(message)

# Loop to save message counts every 60 seconds
@tasks.loop(seconds=60)
async def save_message_counts():
    with open("message_counts.json", "w") as f:
        json.dump(message_counts, f, indent=4)

# Bot startup
@bot.event
async def on_ready():
    save_message_counts.start()
    print(f"✅ Logged in as {bot.user}")

# Command to view message counts
@bot.command(name="message")
async def message(ctx, member: discord.Member = None):
    member = member or ctx.author
    user_id = str(member.id)
    channel_id = str(ctx.channel.id)

    if user_id not in message_counts:
        await ctx.send("❌ No message data found.")
        return

    total = message_counts[user_id]["total"]
    channel_total = message_counts[user_id]["channels"].get(channel_id, 0)

    embed = discord.Embed(
        title=f"📨 Message Count for {member.display_name}",
        color=discord.Color.blurple()
    )
    embed.add_field(name="🧮 Total Messages (All Channels)", value=f"**{total}**", inline=False)
    embed.add_field(name=f"#️⃣ In #{ctx.channel.name}", value=f"**{channel_total}**", inline=False)
    embed.set_footer(text="Tracked by Arcadia Bot")

    await ctx.send(embed=embed)

# -------------------------------------------------------------------------------

AUTORESPONSES_FILE = "autoresponses.json"

# Load or initialize autoresponses
if os.path.exists(AUTORESPONSES_FILE):
    with open(AUTORESPONSES_FILE, "r") as f:
        autoresponses = json.load(f)
else:
    autoresponses = {}

def save_autoresponses():
    with open(AUTORESPONSES_FILE, "w") as f:
        json.dump(autoresponses, f, indent=4)

@bot.command(name="autoresponse")
@commands.has_permissions(manage_messages=True)
async def autoresponse_cmd(ctx, action: str = None, *, args: str = None):
    if action not in ["add", "delete", "list"]:
        await ctx.send("Usage: `$autoresponse add [keyword] | [response] | [#channel (optional)]`\n"
                       "or `$autoresponse delete [keyword]`\n"
                       "or `$autoresponse list`")
        return

    if action == "add":
        if not args or "|" not in args:
            await ctx.send("Usage: `$autoresponse add [keyword] | [response] | [#channel (optional)]`")
            return
        parts = [p.strip() for p in args.split("|")]
        keyword = parts[0].lower()
        response = parts[1]
        channel_id = None

        if len(parts) > 2:
            if parts[2].startswith("<#") and parts[2].endswith(">"):
                try:
                    channel_id = str(int(parts[2][2:-1]))
                except:
                    pass

        autoresponses[keyword] = {"response": response, "channel_id": channel_id}
        save_autoresponses()
        await ctx.send(f"✅ Auto-response for `{keyword}` added.")

    elif action == "delete":
        if not args:
            await ctx.send("Usage: `$autoresponse delete [keyword]`")
            return
        keyword = args.lower()
        if keyword in autoresponses:
            del autoresponses[keyword]
            save_autoresponses()
            await ctx.send(f"🗑️ Auto-response for `{keyword}` deleted.")
        else:
            await ctx.send("❌ Keyword not found.")

    elif action == "list":
        if not autoresponses:
            await ctx.send("No autoresponses set.")
            return

        embed = discord.Embed(title="📃 Auto-Responses", color=discord.Color.blurple())
        for kw, info in autoresponses.items():
            chan = f"<#{info['channel_id']}>" if info['channel_id'] else "Any channel"
            embed.add_field(name=kw, value=f"💬 `{info['response']}`\n🌐 {chan}", inline=False)
        await ctx.send(embed=embed)

# Listener for autoresponses
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()
    for keyword, info in autoresponses.items():
        if keyword in content:
            if info["channel_id"] is None or str(message.channel.id) == info["channel_id"]:
                await message.channel.send(info["response"])
                break

    await bot.process_commands(message)

# ----------------------------------------------------------------------------

async def download_image(url, path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(path, 'wb') as f:
                    f.write(await resp.read())

@bot.command()
async def quote(ctx):
    if not ctx.message.reference:
        return await ctx.send("Please reply to a message to quote it.")

    quoted_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    author = quoted_message.author
    quote_text = quoted_message.content.strip()

    if not quote_text:
        return await ctx.send("The quoted message is empty.")

    # Download avatar
    avatar_url = author.display_avatar.url
    avatar_path = f"/tmp/{author.id}_avatar.png"
    await download_image(avatar_url, avatar_path)

    # Create quote image
    image = Image.new("RGB", (1000, 500), (0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Add avatar
    avatar = Image.open(avatar_path).convert("RGBA").resize((200, 200))
    image.paste(avatar, (100, 150))

    # Load fonts
    font_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    name_font = ImageFont.truetype(font_path_bold, 48)
    handle_font = ImageFont.truetype(font_path, 30)
    quote_font = ImageFont.truetype(font_path, 40)

    # Add text
    draw.text((350, 170), quote_text, font=quote_font, fill="white")
    draw.text((350, 320), author.display_name, font=name_font, fill="white")
    draw.text((350, 380), f"@{author.name}", font=handle_font, fill="gray")

    # Save and send
    output_path = f"/tmp/quote_{ctx.message.id}.png"
    image.save(output_path)

    await ctx.send(file=discord.File(output_path))

    # Cleanup
    os.remove(avatar_path)
    os.remove(output_path)

# ---------------------------

sniped_messages = {}  # {channel_id: [list of dicts]}

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    channel_id = message.channel.id
    sniped_messages.setdefault(channel_id, [])
    sniped_messages[channel_id].insert(0, {
        "content": message.content,
        "author": str(message.author),
        "avatar": message.author.display_avatar.url,
        "time": discord.utils.format_dt(discord.utils.utcnow(), style="R")
    })

    # Limit to last 10 deleted messages per channel
    if len(sniped_messages[channel_id]) > 10:
        sniped_messages[channel_id].pop()

@bot.command()
async def snipe(ctx, amount: int = 1):
    messages = sniped_messages.get(ctx.channel.id, [])
    if not messages:
        await ctx.send("There's nothing to snipe!")
        return

    amount = max(1, min(amount, len(messages)))
    gif_url = "https://i.imgur.com/JxsCfCe.gif"  # Replace with your preferred top-right GIF

    for i in range(amount):
        data = messages[i]
        embed = discord.Embed(
            description=data["content"] or "*No content*",
            color=discord.Color.blurple()
        )
        embed.set_author(name=data["author"], icon_url=data["avatar"])
        embed.set_thumbnail(url=gif_url)
        embed.set_footer(text=f"Deleted {data['time']}")
        await ctx.send(embed=embed)

# ---------------------------------------------------------------------------

CONFESS_CHANNEL_ID = 1364848318034739220  # Replace with your public confession channel
CONFESSION_LOG_CHANNEL_ID = 1364839238960549908  # Replace with your log channel

@bot.command()
async def confess(ctx, *, message=None):
    if message is None:
        await ctx.send("❗ Please include a confession message.\nExample: `$confess I love Noir`")
        return

    confess_channel = bot.get_channel(CONFESS_CHANNEL_ID)
    log_channel = bot.get_channel(CONFESSION_LOG_CHANNEL_ID)

    # Create public embed (no user mention)
    public_embed = discord.Embed(
        title="Arcadia Confession",
        description=message,
        color=discord.Color.purple()
    )
    public_embed.set_footer(text="Submitted anonymously • Powered by Arcadia with love")

    # Create private log embed
    log_embed = discord.Embed(
        title="Confession Logged",
        description=message,
        color=discord.Color.red()
    )
    log_embed.set_author(name=f"{ctx.author} ({ctx.author.id})", icon_url=ctx.author.display_avatar.url)
    log_embed.set_footer(text=f"Sent from: {ctx.guild.name if ctx.guild else 'DMs'}")

    if confess_channel:
        await confess_channel.send(embed=public_embed)

        # If sent in a server channel, delete original message
        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.message.delete()

        # Acknowledge to user (in DM or public)
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("✅ Your confession has been anonymously posted.")
        else:
            try:
                await ctx.author.send("✅ Your confession has been anonymously posted.")
            except discord.Forbidden:
                await ctx.send("✅ Your confession has been posted, but I couldn't DM you.")

    if log_channel:
        await log_channel.send(embed=log_embed)
    else:
        print("⚠️ Log channel not found. Please check CONFESSION_LOG_CHANNEL_ID.")

# --------------------------------------------------------------------------------------

STICKY_FILE = "sticky_messages.json"

if not os.path.exists(STICKY_FILE):
    with open(STICKY_FILE, "w") as f:
        json.dump({}, f)

@bot.event
async def on_ready():
    print(f"Bot is ready. Logged in as {bot.user}")
    refresh_stickies.start()

@tasks.loop(seconds=60)  # Change the interval here
async def refresh_stickies():
    with open(STICKY_FILE, "r") as f:
        data = json.load(f)

    for channel_id, info in data.items():
        channel = bot.get_channel(int(channel_id))
        if not channel:
            continue

        try:
            old_msg = await channel.fetch_message(info["message_id"])
            await old_msg.delete()
        except:
            pass

        try:
            sent = await channel.send(info["message"])
            data[channel_id]["message_id"] = sent.id
        except:
            continue

    with open(STICKY_FILE, "w") as f:
        json.dump(data, f, indent=4)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def sticky(ctx, channel: discord.TextChannel, *, message: str):
    """Set a sticky message for a channel."""
    with open(STICKY_FILE, "r") as f:
        data = json.load(f)

    if str(channel.id) in data:
        try:
            old_msg = await channel.fetch_message(data[str(channel.id)]["message_id"])
            await old_msg.delete()
        except:
            pass

    sent = await channel.send(message)
    data[str(channel.id)] = {"message": message, "message_id": sent.id}

    with open(STICKY_FILE, "w") as f:
        json.dump(data, f, indent=4)

    await ctx.send(f"✅ Sticky message set for {channel.mention}!")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def unsticky(ctx, channel: discord.TextChannel):
    """Remove sticky from a channel."""
    with open(STICKY_FILE, "r") as f:
        data = json.load(f)

    if str(channel.id) in data:
        try:
            msg = await channel.fetch_message(data[str(channel.id)]["message_id"])
            await msg.delete()
        except:
            pass

        del data[str(channel.id)]

        with open(STICKY_FILE, "w") as f:
            json.dump(data, f, indent=4)

        await ctx.send(f"❌ Sticky message removed from {channel.mention}")
    else:
        await ctx.send("No sticky message set in that channel.")

# -----------------------------------------------------------------------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    """Kick a member from the server."""
    try:
        # Try to DM the member first
        try:
            await member.send(f"🚪 You have been kicked from **{ctx.guild.name}**.\nReason: **{reason}**")
        except discord.Forbidden:
            pass  # Ignore if DMs are closed

        # Kick the member
        await member.kick(reason=reason)
        await ctx.send(f"✅ Successfully kicked {member.mention} for: **{reason}**")

        # Send a log message to the log channel
        log_channel = bot.get_channel(1364839238960549908)
        if log_channel:
            log_embed = discord.Embed(
                title="Kick Action",
                color=discord.Color.red()
            )
            log_embed.add_field(name="Member", value=member.mention, inline=False)
            log_embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            log_embed.add_field(name="Reason", value=reason, inline=False)
            log_embed.timestamp = discord.utils.utcnow()
            await log_channel.send(embed=log_embed)

    except Exception as e:
        await ctx.send(f"❌ Failed to kick {member.mention}. Error: {e}")

# ----------------------------------------------------------------------------
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    """Ban a member from the server."""
    try:
        # Try to DM the member first
        try:
            await member.send(f"🔨 You have been banned from **{ctx.guild.name}**.\nReason: **{reason}**")
        except discord.Forbidden:
            pass  # Ignore if DMs are closed

        # Ban the member
        await member.ban(reason=reason)
        await ctx.send(f"✅ Successfully banned {member.mention} for: **{reason}**")

        # Send a log message to the log channel
        log_channel = bot.get_channel(1364839238960549908)
        if log_channel:
            log_embed = discord.Embed(
                title="Ban Action",
                color=discord.Color.dark_red()
            )
            log_embed.add_field(name="Member", value=member.mention, inline=False)
            log_embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            log_embed.add_field(name="Reason", value=reason, inline=False)
            log_embed.timestamp = discord.utils.utcnow()
            await log_channel.send(embed=log_embed)

    except Exception as e:
        await ctx.send(f"❌ Failed to ban {member.mention}. Error: {e}")
# ------------------------------------------------------------------------------

# Your log channel ID
LOG_CHANNEL_ID = 1364839238960549908

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, time: str, *, reason="No reason provided."):
    try:
        time = time.lower()
        seconds = 0
        if time.endswith("min"):
            seconds = int(time[:-3]) * 60
        elif time.endswith("hr"):
            seconds = int(time[:-2]) * 60 * 60
        elif time.endswith("d"):
            seconds = int(time[:-1]) * 60 * 60 * 24
        else:
            await ctx.send("❌ Invalid time format! Use formats like `10min`, `2hr`, or `1d`.")
            return

        if seconds <= 0 or seconds > 2419200:
            await ctx.send("❌ Timeout must be between 1 second and 28 days.")
            return

        await member.timeout(timedelta(seconds=seconds), reason=reason)
        await ctx.send(f"✅ {member.mention} has been timed out for **{time}**. Reason: {reason}")

        try:
            await member.send(f"🚫 You have been timed out in **{ctx.guild.name}** for **{time}**.\nReason: {reason}")
        except discord.Forbidden:
            pass  # can't DM

        # Send a log message to the log channel
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="Timeout Action",
                color=discord.Color.orange()
            )
            log_embed.add_field(name="Member", value=member.mention, inline=False)
            log_embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            log_embed.add_field(name="Duration", value=time, inline=False)
            log_embed.add_field(name="Reason", value=reason, inline=False)
            log_embed.timestamp = discord.utils.utcnow()
            await log_channel.send(embed=log_embed)

    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

# -----------------------------------------------------------------------------

afk_users = {}

@bot.command(aliases=['away'])
async def afk(ctx, *, reason=None):
    """Sets your status to AFK."""
    user_id = ctx.author.id
    global afk_users
    if user_id in afk_users:
        await ctx.send("👋 Welcome back! Your AFK status has been removed.")
        del afk_users[user_id]
        # You could also revert their nickname here if you changed it
        try:
            if ctx.author.nick and ctx.author.nick.startswith("[AFK] "):
                await ctx.author.edit(nick=ctx.author.nick[6:])
        except discord.Forbidden:
            await ctx.send("⚠️ Could not change your nickname back due to permission issues.")
        return

    afk_users[user_id] = {"reason": reason, "time": datetime.datetime.utcnow()}

    afk_embed = discord.Embed(
        title="😴 Going AFK...",
        color=0xADD8E6  # Light blue for a calm aesthetic
    )
    afk_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    if reason:
        afk_embed.add_field(name="Reason", value=reason, inline=False)
    afk_embed.timestamp = datetime.datetime.utcnow()
    await ctx.send(embed=afk_embed)

    # Optional: Change nickname to indicate AFK
    try:
        await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}")
    except discord.Forbidden:
        await ctx.send("⚠️ Could not change your nickname to indicate AFK due to permission issues.")

@bot.listen('on_message')
async def on_message_afk_check(message):
    if message.author.bot:
        return
    user_id = message.author.id
    global afk_users
    if user_id in afk_users:
        await message.channel.send(f"👋 Welcome back, {message.author.mention}! Your AFK status has been removed.", delete_after=5)
        del afk_users[user_id]
        try:
            if message.author.nick and message.author.nick.startswith("[AFK] "):
                await message.author.edit(nick=message.author.nick[6:])
        except discord.Forbidden:
            pass
        return

    for member in message.mentions:
        if member.id in afk_users:
            afk_info = afk_users[member.id]
            reason = afk_info["reason"]
            time_diff = datetime.datetime.utcnow() - afk_info["time"]
            minutes = int(time_diff.total_seconds() // 60)
            time_ago = f"{minutes} minute{'s' if minutes != 1 else ''} ago"

            reply = f"💤 **{member.display_name}** is currently AFK"
            if reason:
                reply += f" with the reason: {reason}"
            reply += f" (since {time_ago})."
            await message.channel.send(reply, delete_after=5)


keep_alive()
bot.run(TOKEN)
