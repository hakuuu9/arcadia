import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import random
import math
import asyncio
import json
import re
import os
import html
import time
import datetime
import textwrap
import aiohttp
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import io
import requests
from collections import defaultdict
from config import TOKEN, GUILD_ID, ROLE_ID, VANITY_LINK, LOG_CHANNEL_ID, VANITY_IMAGE_URL
from keep_alive import keep_alive
from datetime import datetime, timedelta
from discord.ext import commands
import discord

intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix="$", intents=intents)

# Apply rate limit to all commands
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Apply the global cooldown
@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)  # 1 command per 10 seconds per user
async def test(ctx):
    await ctx.send("This is a test command!")

# Handle cooldown error (optional)
@test.error
async def test_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Please wait {error.retry_after:.2f} seconds before using that command again.")


# The ID of the channel to log vanity role grants and removals
VANITY_LOG_CHANNEL_ID = 1363396246663860356

# The ID of the role to grant for having the vanity link
ROLE_ID = 1361732154584858724  # Replace with the actual Role ID

# The specific vanity link to check for in the custom status
VANITY_LINK = "discord.gg/warcadia"  # Replace with your actual vanity link

# The URL of the image to embed when the role is granted
VANITY_IMAGE_URL = 'https://cdn.discordapp.com/attachments/1365065762104020992/1371819836908503122/Recording_2025-05-13_195956.gif'

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

            vanity_log_channel = bot.get_channel(VANITY_LOG_CHANNEL_ID)
            if vanity_log_channel:
                await vanity_log_channel.send(embed=embed)

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

            vanity_log_channel = bot.get_channel(VANITY_LOG_CHANNEL_ID)
            if vanity_log_channel:
                await vanity_log_channel.send(embed=embed)

    except Exception as e:
        print(f"[Error - Vanity Role Handler]: {e}")

# ----------------------------------------------------------------------

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
async def role(ctx, member: discord.Member = None, *, role_input: str = None):
    STAFF_ROLE_NAME = "Moderator"
    STAFF_ROLE_ID = 1347181345922748456
    LOG_CHANNEL_ID = 1364839238960549908

    staff_role = discord.utils.get(ctx.guild.roles, name=STAFF_ROLE_NAME)

    if not staff_role or staff_role.id != STAFF_ROLE_ID:
        await ctx.send("❌ You don't have the required staff role.")
        return
    if STAFF_ROLE_ID not in [role.id for role in ctx.author.roles]:
        await ctx.send("❌ You don't have permission to use this command.")
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

    granted_emoji = "<a:GC_Fire:1348482027447386116>"
    revoked_emoji = "<a:calcifer:1348189333542404106>"

    embed = discord.Embed(
        color=discord.Color.blurple(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url="https://i.imgur.com/JxsCfCe.gif")
    embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

    if role in member.roles:
        await member.remove_roles(role)
        embed.title = f"{revoked_emoji} Role Revoked"
        embed.description = (
            f"The role **{role.name}** has been revoked from {member.mention}.\n"
            f"All permissions associated with this role have been removed."
        )
    else:
        await member.add_roles(role)
        embed.title = f"{granted_emoji} Role Granted"
        embed.description = (
            f"{member.mention} has been granted the **{role.name}** role.\n"
            f"Relevant permissions are now active."
        )

    await ctx.send(embed=embed)

    log_channel = ctx.guild.get_channel(LOG_CHANNEL_ID)
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
            title="📖 Arcadian Bot Command Info (Page 1/3)",
            description="Explore all my features, games, utilities, and more!",
            color=discord.Color.purple()
        ).add_field(
            name="👥🎉 Member Commands",
            value=(
                "**🎲 `$choose option1, option2`** — Randomly choose one\n"
                "**🖼️ `$avatar [@user]`** — View a user's avatar\n"
                "**🎱 `$8b question`** — Magic 8-Ball answers\n"
                "**⏰ `$remind [time] [task]`** — Set a reminder\n"
                "**🧑‍💻 `$userinfo [@user]`** — Display user info\n"
                "**🕊️ `$confess your message`** — Anonymous confession (with private logging)\n"
            ),
            inline=False
        ).set_thumbnail(url="https://i.imgur.com/JxsCfCe.gif"),

        discord.Embed(
            title="🎮 Arcadian Bot Command Info (Page 2/3)",
            description="Time to play!",
            color=discord.Color.purple()
        ).add_field(
            name="🎮 Fun Commands",
            value=(
                "**🎲 `$rps @user`** — Rock-Paper-Scissors\n"
                "**🎯 `$hangman solo/duo/free`** — Hangman modes\n"
                "**❌ `$tictactoe @user`** — Play Tic Tac Toe\n"
            ),
            inline=False
        ).set_thumbnail(url="https://i.imgur.com/JxsCfCe.gif"),

        discord.Embed(
            title="🛠️ Arcadian Bot Command Info (Page 3/3)",
            description="Useful tools and utilities.",
            color=discord.Color.purple()
        ).add_field(
            name="🔧 Utility Commands",
            value=(
                "**👀 `$snipe`** — Retrieve the last deleted message\n"
                "**🔀 `$randomvc`** — Join a random public voice channel (excluding private ones)\n"
                "**🎧 `$np`** — Display the currently playing song from Spotify\n"  
            ),
            inline=False
        ).set_thumbnail(url="https://i.imgur.com/JxsCfCe.gif"),
    ]

    current_page = 0
    total_pages = len(pages)

    class PaginatorView(View):
        def __init__(self):
            super().__init__(timeout=300)
            self.value = None
            self.page = current_page

        @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
        async def previous(self, interaction: discord.Interaction, button: Button):
            if interaction.user != ctx.author:
                await interaction.response.send_message("Only the command user can use this.", ephemeral=True)
                return
            self.page = (self.page - 1) % total_pages
            await interaction.response.edit_message(embed=pages[self.page], view=self)

        @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
        async def next(self, interaction: discord.Interaction, button: Button):
            if interaction.user != ctx.author:
                await interaction.response.send_message("Only the command user can use this.", ephemeral=True)
                return
            self.page = (self.page + 1) % total_pages
            await interaction.response.edit_message(embed=pages[self.page], view=self)

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

    embed.set_thumbnail(url="https://i.imgur.com/JxsCfCe.gif")

    embed.add_field(
        name="🧰 Moderation & Support Tools (1/2)",
        value=(
            "📩 `$createembed #channel | title | description | #hexcolor`\n"
            "🎭 `$role @member @role`\n"
            "📊 `$serverinfo`\n"
            "🧹 `$purge [amount]`\n"
            "⚠️ `$warn @user reason`\n"
            "📌 `$inrole`\n"
            "📊 `$arclb`\n"
            "📊 `$sticky #channel your message`\n"
            "📊 `$unsticky #channel`\n"
            "👢 `$kick @user reason`\n"
            "🔨 `$ban @user reason`\n"
        ),
        inline=False
    )

    embed.add_field(
        name="🧰 Moderation & Support Tools (2/2)",
        value=(
            "🔇 `$timeout @user seconds reason`\n"
            "📝 `$post #channel / embed/normal / message / interval`\n"
            "🛑 `$unpost #channel`\n"
            "📤 `$dm @user | message`\n"
            "📤 `$dm @role | message`\n"
            "📩 `$sms [user_id] [message]`\n"
            "💬 `$chat #channel text`\n"
         
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

# --------------------------------------------------------------------------

# Tic Tac Toe Setup
active_ttt_games = {}
reaction_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]

@bot.command(name="tictactoe")
async def tictactoe(ctx, opponent: discord.Member):
    if ctx.author == opponent:
        return await ctx.send("❌ You can't play against yourself!")
    if opponent.bot:
        return await ctx.send("🤖 You can't play against a bot!")

    game_id = f"{ctx.channel.id}-{ctx.author.id}-{opponent.id}"
    if game_id in active_ttt_games:
        return await ctx.send("⚠️ A Tic Tac Toe game is already running between you two in this channel.")

    board = [None] * 9  # Use None for empty cells
    players = [ctx.author, opponent]
    symbols = ["❌", "⭕"]
    current_turn = 0

    game_data = {
        "board": board,
        "players": players,
        "symbols": symbols,
        "turn": current_turn,
        "message": None  # To store the board message
    }
    active_ttt_games[game_id] = game_data

    board_message = await ctx.send(render_board(board, players, symbols, current_turn))
    game_data["message"] = board_message

    for emoji in reaction_emojis:
        await board_message.add_reaction(emoji)


@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    if str(reaction.emoji) not in reaction_emojis:
        return
    if reaction.message.author != bot.user:
        return

    game_id_match = None
    for gid, data in active_ttt_games.items():
        if data["message"] and data["message"].id == reaction.message.id:
            # Ensure the game is between the reactor and one of the players
            if user in data["players"]:
                game_id_match = gid
                break

    if not game_id_match:
        return

    game = active_ttt_games[game_id_match]
    current_player = game["players"][game["turn"]]
    if user != current_player:
        await reaction.message.remove_reaction(reaction.emoji, user)
        return

    position = reaction_emojis.index(str(reaction.emoji))
    if game["board"][position] is not None:
        await reaction.message.remove_reaction(reaction.emoji, user)
        return

    game["board"][position] = game["symbols"][game["turn"]]

    await reaction.message.clear_reactions()
    await reaction.message.edit(content=render_board(game["board"], game["players"], game["symbols"], game["turn"]))

    if check_win(game["board"], game["symbols"][game["turn"]]):
        await reaction.message.edit(content=render_board(game["board"], game["players"], game["symbols"], game["turn"]) + f"\n🏆 {current_player.mention} wins!")
        del active_ttt_games[game_id_match]
        return

    if all(cell is not None for cell in game["board"]):
        await reaction.message.edit(content=render_board(game["board"], game["players"], game["symbols"], game["turn"]) + "\n🤝 It's a draw!")
        del active_ttt_games[game_id_match]
        return

    game["turn"] = 1 - game["turn"]
    await reaction.message.edit(content=render_board(game["board"], game["players"], game["symbols"], game["turn"]) + f"\n➡️ {game['players'][game['turn']].mention}'s turn!")

    for emoji in reaction_emojis:
        if game["board"][reaction_emojis.index(emoji)] is None:
            await reaction.message.add_reaction(emoji)


def render_board(board, players, symbols, turn):
    grid = "```\n"
    for i in range(9):
        if board[i] is None:
            grid += str(i + 1)
        else:
            grid += board[i]
        if (i + 1) % 3 == 0:
            grid += "|\n"
            if i < 8:
                grid += "|--- --- ---|\n"
        else:
            grid += " | "
    grid += "```"
    turn_msg = f"🎮 Tic Tac Toe: {players[0].mention} ({symbols[0]}) vs {players[1].mention} ({symbols[1]})\n\n" + grid
    turn_msg += f"\n⬆️ {players[turn].mention}'s turn! Click a reaction to make your move."
    return turn_msg


def check_win(board, symbol):
    wins = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
        [0, 4, 8], [2, 4, 6]              # diagonals
    ]
    return any(all(board[i] == symbol for i in combo) for combo in wins)

# ---------------------------------------------------------------------------------

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

# ------------------------------------------------------------------------------------------

# Replace with your mod log channel ID
MODLOG_CHANNEL_ID = 1350497918574006282
# Channel where warned users are mentioned
TALK_CHANNEL_ID = 1363918605678411807
# "Warned" role that lets users see the warning channel
WARNED_ROLE_ID = 1363911975016333402
# The specific role ID that can use the warn command
ALLOWED_WARN_ROLE_ID = 1347181345922748456  # Replace with the actual role ID

def is_allowed_warn_role():
    async def predicate(ctx):
        if ctx.guild:
            role = ctx.guild.get_role(ALLOWED_WARN_ROLE_ID)
            if role and role in ctx.author.roles:
                return True
        return False
    return commands.check(predicate)

@bot.command()
@is_allowed_warn_role()
async def warn(ctx, member: discord.Member, *, reason: str = "No reason provided."):
    """Warn a member in the server."""
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

@warn.error
async def warn_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("⚠️ You do not have the required role to use the warn command.")
    else:
        print(f"Error in warn command: {error}")
        await ctx.send("❌ An unexpected error occurred while trying to warn.")



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

# --------------------------------------------------------------------------------------------------

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

# Constants
LOG_CHANNEL_ID = 1364839238960549908
ALLOWED_KICK_ROLE_ID = 1347181345922748456

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

def is_allowed_kick_role():
    async def predicate(ctx):
        if ctx.guild:
            role = ctx.guild.get_role(ALLOWED_KICK_ROLE_ID)
            if role and role in ctx.author.roles:
                return True
        return False
    return commands.check(predicate)

@bot.command()
@is_allowed_kick_role()
async def kick(ctx, user: str, *, reason: str = ""):
    # Ensure reason is provided with ?r
    if not reason.startswith('?r ') or len(reason[3:].strip()) == 0:
        await ctx.send("❌ Please provide a reason using `?r <reason>`.")
        return
    reason = reason[3:].strip()

    # Get the member object
    try:
        if user.startswith("<@") and user.endswith(">"):
            user_id = int(user.strip("<@!>"))
        else:
            user_id = int(user)
        member = await ctx.guild.fetch_member(user_id)
    except Exception:
        await ctx.send("❌ Invalid user mention or ID.")
        return

    try:
        # Try to DM the member first
        allowed_role = ctx.guild.get_role(ALLOWED_KICK_ROLE_ID)
        role_name = allowed_role.name if allowed_role else "Staff"

        try:
            await member.send(
                f"🚪 You have been kicked from **{ctx.guild.name}**.\n"
                f"Reason: {reason}\n\n"
            )
        except discord.Forbidden:
            pass  # DMs closed

        await member.kick(reason=reason)
        await ctx.send(f"✅ Successfully kicked {member.mention}.\nReason: {reason}")

        # Log the kick
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(title="Kick Action", color=discord.Color.red())
            log_embed.add_field(name="Member", value=member.mention, inline=False)
            log_embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            log_embed.add_field(name="Reason", value=reason, inline=False)
            log_embed.timestamp = discord.utils.utcnow()
            await log_channel.send(embed=log_embed)

    except Exception as e:
        await ctx.send(f"❌ Failed to kick user. Error: {e}")

@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("⚠️ You do not have permission to use this command.")
    else:
        print(f"Error in kick command: {error}")
        await ctx.send("$kick @user ?r Inappropriate language in chat")

# ----------------------------------------------------------------------------

# Constants
LOG_CHANNEL_ID = 1364839238960549908
ALLOWED_BAN_ROLE_ID = 1347181345922748456

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

def is_allowed_ban_role():
    async def predicate(ctx):
        if ctx.guild:
            role = ctx.guild.get_role(ALLOWED_BAN_ROLE_ID)
            if role and role in ctx.author.roles:
                return True
        return False
    return commands.check(predicate)

@bot.command()
@is_allowed_ban_role()
async def ban(ctx, user: str, *, reason: str = ""):
    # Make sure reason is provided and starts with ?r
    if not reason.startswith('?r ') or len(reason[3:].strip()) == 0:
        await ctx.send("❌ Please provide a reason using `?r <reason>`.")
        return
    reason = reason[3:].strip()

    # Try to resolve the user
    try:
        if user.startswith("<@") and user.endswith(">"):
            user_id = int(user.strip("<@!>"))
        else:
            user_id = int(user)
        member = await ctx.guild.fetch_member(user_id)
    except Exception:
        await ctx.send("❌ Invalid user mention or ID.")
        return

    try:
        # Try to DM the user
        allowed_role = ctx.guild.get_role(ALLOWED_BAN_ROLE_ID)
        role_name = allowed_role.name if allowed_role else "Staff"

        try:
            await member.send(
                f"🔨 You have been banned from **{ctx.guild.name}**.\n"
                f"Reason: {reason}\n\n"
            )
        except discord.Forbidden:
            pass  # DMs closed

        # Ban the user
        await member.ban(reason=reason)
        await ctx.send(f"✅ Successfully banned {member.mention}.\nReason: {reason}")

        # Log the action
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(title="Ban Action", color=discord.Color.dark_red())
            log_embed.add_field(name="Member", value=member.mention, inline=False)
            log_embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            log_embed.add_field(name="Reason", value=reason, inline=False)
            log_embed.timestamp = discord.utils.utcnow()
            await log_channel.send(embed=log_embed)

    except Exception as e:
        await ctx.send(f"❌ Failed to ban user. Error: {e}")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("⚠️ You do not have permission to use this command.")
    else:
        print(f"Error in ban command: {error}")
        await ctx.send("$ban @user ?r Repeated rule violations")

# ------------------------------------------------------------------------------

# Constants
LOG_CHANNEL_ID = 1364839238960549908
ALLOWED_TIMEOUT_ROLE_ID = 1347181345922748456

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

def is_allowed_timeout_role():
    async def predicate(ctx):
        if ctx.guild:
            role = ctx.guild.get_role(ALLOWED_TIMEOUT_ROLE_ID)
            if role and role in ctx.author.roles:
                return True
        return False
    return commands.check(predicate)

@bot.command()
@is_allowed_timeout_role()
async def timeout(ctx, user: str, duration: str, *, reason: str = ""):
    # Ensure reason is provided using ?r
    if not reason.startswith('?r ') or len(reason[3:].strip()) == 0:
        await ctx.send("❌ Please provide a reason using `?r <reason>`.")
        return
    reason = reason[3:].strip()

    # Get the member object
    try:
        if user.startswith("<@") and user.endswith(">"):
            user_id = int(user.strip("<@!>"))
        else:
            user_id = int(user)
        member = await ctx.guild.fetch_member(user_id)
    except Exception:
        await ctx.send("❌ Invalid user mention or ID.")
        return

    # Parse time
    duration = duration.lower()
    seconds = 0
    try:
        if duration.endswith(("sec", "secs")):
            seconds = int(duration.rstrip("secs").rstrip("sec"))
        elif duration.endswith(("min", "mins")):
            seconds = int(duration.rstrip("mins").rstrip("min")) * 60
        elif duration.endswith(("hr", "hrs")):
            seconds = int(duration.rstrip("hrs").rstrip("hr")) * 3600
        elif duration.endswith(("d", "days")):
            seconds = int(duration.rstrip("days").rstrip("d")) * 86400
        else:
            await ctx.send("❌ Invalid time format! Use `60sec`, `5min`, `2hr`, or `1d`.")
            return
    except ValueError:
        await ctx.send("❌ Invalid duration format.")
        return

    if seconds <= 0 or seconds > 2419200:
        await ctx.send("❌ Timeout must be between 1 second and 28 days.")
        return

    # Attempt to timeout
    try:
        await member.timeout(timedelta(seconds=seconds), reason=reason)
        await ctx.send(f"✅ {member.mention} has been timed out for **{duration}**.\nReason: {reason}")

        # Get staff role name
        allowed_role = ctx.guild.get_role(ALLOWED_TIMEOUT_ROLE_ID)
        role_name = allowed_role.name if allowed_role else "Staff"

        try:
            await member.send(
                f"🚫 You have been timed out in **{ctx.guild.name}** for **{duration}**.\n"
                f"Reason: {reason}\n\n"
                f"If you believe this was a mistake, you may reach out to **{role_name}**."
            )
        except discord.Forbidden:
            pass  # Can't DM

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(title="Timeout Issued", color=discord.Color.orange())
            log_embed.add_field(name="Member", value=member.mention, inline=False)
            log_embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            log_embed.add_field(name="Duration", value=duration, inline=False)
            log_embed.add_field(name="Reason", value=reason, inline=False)
            log_embed.timestamp = discord.utils.utcnow()
            await log_channel.send(embed=log_embed)

    except Exception as e:
        await ctx.send(f"⚠️ Failed to timeout user: {e}")

@timeout.error
async def timeout_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("⚠️ You do not have permission to use this command.")
    else:
        await ctx.send("$timeout @User 10mins ?r spamming in general")
        print(f"Error in timeout command: {error}")

# -----------------------------------------------------------------------------

CONFESS_CHANNEL_ID = 1364848318034739220  # Replace with your public confession channel ID
CONFESSION_LOG_CHANNEL_ID = 1364839238960549908  # Replace with your confession log channel ID

@bot.command()
async def confess(ctx, *, message=None):
    if message is None:
        await ctx.send("❗ Please include a confession message.\nExample: `$confess I love Noir`")
        return

    confess_channel = bot.get_channel(CONFESS_CHANNEL_ID)
    log_channel = bot.get_channel(CONFESSION_LOG_CHANNEL_ID)

    # Create public confession embed
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

        # Delete original message if sent inside a server
        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.message.delete()

        # Try to DM the user silently (no error message if failed)
        try:
            await ctx.author.send("✅ Your confession has been anonymously posted.")
        except discord.Forbidden:
            pass  # Do nothing if DMs are locked

    if log_channel:
        await log_channel.send(embed=log_embed)
    else:
        print("⚠️ Log channel not found. Please check CONFESSION_LOG_CHANNEL_ID.")

# --------------------------------------------------------------------------------------

sticky_messages = {}

@bot.command()
@commands.has_permissions(manage_messages=True)
async def sticky(ctx, channel: discord.TextChannel, *, message: str):
    await ctx.send(f"✅ Sticky message set for {channel.mention}!")
    
    # Define a helper function to send the sticky message
    async def send_sticky(channel, message):
        await bot.wait_until_ready()

        # Re-send the sticky message every time a member sends a message
        async def on_message(message):
            # Ignore the bot's own messages
            if message.author == bot.user:
                return

            # Delete the previous sticky if it exists
            if channel.id in sticky_messages:
                try:
                    previous_message = await channel.fetch_message(sticky_messages[channel.id])
                    await previous_message.delete()
                except Exception:
                    pass  # Ignore if the message can't be found or deleted

            # Send the new sticky message
            # If the message is an embed
            if isinstance(message, discord.Embed):
                new_message = await channel.send(embed=message)
            else:
                # Support server emojis in the text message
                new_message = await channel.send(message)

            # Store the new sticky message ID
            sticky_messages[channel.id] = new_message.id

        # Add the on_message listener to the bot
        bot.add_listener(on_message)

    # Start the sticky message task
    bot.loop.create_task(send_sticky(channel, message))

@bot.command()
@commands.has_permissions(manage_messages=True)
async def unsticky(ctx, channel: discord.TextChannel):
    if channel.id in sticky_messages:
        try:
            # Try to fetch and delete the current sticky message
            sticky_message = await channel.fetch_message(sticky_messages[channel.id])
            await sticky_message.delete()
            del sticky_messages[channel.id]
            await ctx.send(f"✅ Sticky message has been removed from {channel.mention}.")
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")
    else:
        await ctx.send("❌ No sticky message found in that channel.")

# ------------------------------------------------------------------------

# Store posted messages and tasks
posted_messages = {}
post_tasks = {}

@bot.command()
@commands.has_permissions(manage_messages=True)
async def post(ctx, *, args: str):
    """
    Post a message that will automatically repost after an interval.
    Usage:
    $post <channel id or mention> / <embed/normal> / <interval> / <message>
    Example:
    $post #1234567890 / embed / 1min / Hello Arcadia!\nHow are you today?
    """

    args = [arg.strip() for arg in args.split('/', 3)]  # split into 4 parts only

    if len(args) != 4:
        await ctx.send("❗ Please follow the format: `$post <channel id> / <embed/normal> / <interval> / <message>`")
        return

    channel_input, option, interval, message = args

    # Parse the channel
    try:
        if channel_input.startswith('<#') and channel_input.endswith('>'):
            channel_id = int(channel_input[2:-1])
        else:
            channel_id = int(channel_input)
        channel = bot.get_channel(channel_id)
        if channel is None:
            raise ValueError
    except ValueError:
        await ctx.send("❗ Invalid channel ID or mention.")
        return

    if option.lower() not in ['embed', 'normal']:
        await ctx.send("❗ Please specify 'embed' or 'normal' for the message type.")
        return

    # Parse interval
    time_interval = parse_interval(interval)
    if time_interval is None:
        await ctx.send("❗ Invalid interval format. Use '1min', '60sec', '1d', '1hr', etc.")
        return

    # Replace \n with real newlines
    message = message.replace("\\n", "\n")

    # Send first message
    if option.lower() == 'embed':
        embed = discord.Embed(description=message, color=discord.Color.from_rgb(0, 0, 0))  # black color
        embed.set_footer(text="Posted by Arcadia Bot")
        posted_message = await channel.send(embed=embed)
    else:
        posted_message = await channel.send(message)

    posted_messages[channel.id] = posted_message

    await ctx.send(f"✅ Your message has been posted in {channel.mention} and will repost every **{interval}**.")

    await ctx.message.delete()

    # Start the repost loop
    async def repost_loop():
        while True:
            await asyncio.sleep(time_interval.total_seconds())
            try:
                await posted_messages[channel.id].delete()
            except Exception as e:
                print(f"Error deleting old message: {e}")

            if option.lower() == 'embed':
                embed = discord.Embed(description=message, color=discord.Color.from_rgb(0, 0, 0))
                embed.set_footer(text="Posted by Arcadia Bot")
                new_message = await channel.send(embed=embed)
            else:
                new_message = await channel.send(message)

            posted_messages[channel.id] = new_message
            print(f"✅ Message reposted in {channel.name}.")

    task = asyncio.create_task(repost_loop())
    post_tasks[channel.id] = task

def parse_interval(interval):
    """Parse intervals like 1min, 60sec, 1d, 1hr."""
    import re
    from datetime import timedelta

    pattern = re.compile(r"(\d+)([a-zA-Z]+)")
    match = pattern.match(interval)
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2).lower()

    if unit in ['sec', 's', 'second']:
        return timedelta(seconds=value)
    elif unit in ['min', 'm', 'minute']:
        return timedelta(minutes=value)
    elif unit in ['hr', 'h', 'hour']:
        return timedelta(hours=value)
    elif unit in ['day', 'd']:
        return timedelta(days=value)
    else:
        return None


# --------------------------------------------------------------

# Dictionary to store running tasks
post_tasks = {}

@bot.command()
async def unpost(ctx, *, channel_input: str):
    """
    Stop reposting a message in the given channel.
    Usage:
    $unpost <channel id or mention>
    """
    try:
        if channel_input.startswith('<#') and channel_input.endswith('>'):
            channel_id = int(channel_input[2:-1])
        else:
            channel_id = int(channel_input)

        channel = bot.get_channel(channel_id)

        if channel_id in post_tasks:
            post_tasks[channel_id].cancel()  # Cancel the repeating task
            del post_tasks[channel_id]       # Remove from tracking
            await ctx.send(f"🛑 Stopped reposting messages in {channel.mention}.")
        else:
            await ctx.send("❗ There's no active post in that channel.")
    
    except ValueError:
        await ctx.send("❗ Invalid channel ID or mention.")

# ---------------------------------------------------------------------------
                      # arcadia and solana autoreact
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()

    # Emojis by ID
    arcadia1 = bot.get_emoji(1348189333542404106)
    arcadia2 = bot.get_emoji(1366767618123370497)
    solana1 = bot.get_emoji(1366765591305912360)
    solana2 = bot.get_emoji(1366765657177325608)
    heaven1 = bot.get_emoji(1369139903182671964)  # Replace with actual ID
    heaven2 = bot.get_emoji(1369152680169308281)  # Replace with actual ID

    # React to keywords
    if "arcadia" in content:
        if arcadia1: await message.add_reaction(arcadia1)
        if arcadia2: await message.add_reaction(arcadia2)
    if "solana" in content:
        if solana1: await message.add_reaction(solana1)
        if solana2: await message.add_reaction(solana2)
    if "heaven" in content:
        if heaven1: await message.add_reaction(heaven1)
        if heaven2: await message.add_reaction(heaven2)

    await bot.process_commands(message)


# ----------------------------------------------------------------------------

# Helper function to download image
async def download_image(url, filepath):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(filepath, 'wb') as f:
                    f.write(await resp.read())

# Helper function to wrap text
def draw_wrapped_text(draw, text, font, x, y, width, max_height, line_height):
    wrapped_text = textwrap.fill(text, width=width)
    y_offset = y
    for line in wrapped_text.split('\n'):
        if y_offset + line_height > max_height:
            break
        draw.text((x, y_offset), line, font=font, fill="white")
        y_offset += line_height

@bot.command()
async def profilecard(ctx, member: discord.Member = None):
    member = member or ctx.author

    # Get avatar and banner
    avatar_url = member.display_avatar.url
    avatar_path = f"/tmp/{member.id}_avatar.png"
    await download_image(avatar_url, avatar_path)

    banner_url = member.banner.url if member.banner else None
    if banner_url:
        banner_path = f"/tmp/{member.id}_banner.png"
        await download_image(banner_url, banner_path)
    else:
        banner_path = None

    # Create the background
    width, height = 1000, 500
    if banner_path:
        banner = Image.open(banner_path).resize((width, height))
        base = banner
    else:
        bg = Image.open(avatar_path).convert("RGB").resize((width, height))
        blur = bg.filter(ImageFilter.GaussianBlur(18))
        overlay = Image.new("RGBA", blur.size, (0, 0, 0, 180))
        base = Image.alpha_composite(blur.convert("RGBA"), overlay)

    draw = ImageDraw.Draw(base)

    font_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    name_font = ImageFont.truetype(font_path_bold, 40)
    username_font = ImageFont.truetype(font_path, 30)
    info_font = ImageFont.truetype(font_path, 25)
    role_font = ImageFont.truetype(font_path, 22)
    footer_font = ImageFont.truetype(font_path, 18)
    badge_font = ImageFont.truetype(font_path, 30)

    # Display avatar (rounded)
    avatar = Image.open(avatar_path).convert("RGBA").resize((180, 180))
    mask = Image.new("L", (180, 180), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, 180, 180), fill=255)
    base.paste(avatar, (70, 160), mask)

    # Name and username
    name_text = f"{member.display_name}"
    name_x, name_y = 280, 140
    draw.text((name_x, name_y), name_text, font=name_font, fill="white")

    name_bbox = draw.textbbox((name_x, name_y), name_text, font=name_font)
    username_y = name_bbox[3] + 5
    draw.text((name_x, username_y), f"@{member.name}", font=username_font, fill="lightgray")

    # Highest role icon badge (excluding @everyone)
    roles_with_icons = [r for r in member.roles if r.icon and r != ctx.guild.default_role]
    top_role = max(roles_with_icons, key=lambda r: r.position, default=None)

    if top_role:
        role_icon_url = top_role.icon.url
        role_icon_path = f"/tmp/{member.id}_roleicon.png"
        await download_image(role_icon_url, role_icon_path)

        badge_icon = Image.open(role_icon_path).convert("RGBA").resize((40, 40))
        badge_x = name_bbox[2] + 15
        base.paste(badge_icon, (badge_x, name_y), badge_icon)

        os.remove(role_icon_path)

    # Account and join dates
    created = member.created_at.strftime("%b %d, %Y")
    joined = member.joined_at.strftime("%b %d, %Y") if member.joined_at else "Unknown"
    draw.text((280, username_y + 40), f"Created: {created}", font=info_font, fill="lightgray")
    draw.text((280, username_y + 70), f"Joined: {joined}", font=info_font, fill="lightgray")

    # Roles (top 5, excluding @everyone)
    roles = [r for r in member.roles if r.name != "@everyone"]
    top_roles = sorted(roles, key=lambda r: r.position, reverse=True)[:5]
    y_offset = username_y + 110
    line_height = 25
    for i, role in enumerate(top_roles):
        if y_offset + line_height * (i + 1) > height - 50:
            break
        draw.text((280, y_offset + line_height * i), f"• {role.name}", font=role_font, fill=role.color.to_rgb())

    # Footer
    footer_text = "discord.gg/arcadiasolana"
    draw.text((width - 370, height - 30), footer_text, font=footer_font, fill=(30, 215, 96))

    # Save & send
    output_path = f"/tmp/profilecard_{member.id}.png"
    base.convert("RGB").save(output_path)
    await ctx.send(file=discord.File(output_path))

    # Clean up
    os.remove(avatar_path)
    if banner_path:
        os.remove(banner_path)

# ----------------------------------------------------------------

# Define the log channel ID and specific channels to react in
LOG_REACT_ID = 1364839238960549908  # Replace with your actual log channel ID
REACT_CHANNEL_IDS = [1357663704883396728, 1365257223747534858]  # Replace with your two target channel IDs

# Store the emoji globally
auto_react_emoji = None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    autoreact_loop.start()

@bot.command()
async def setreact(ctx, emoji: str):
    """Set the emoji to be used for auto-reaction."""
    global auto_react_emoji
    auto_react_emoji = emoji
    await ctx.send(f"✅ Auto-react emoji set to {emoji}")

@tasks.loop(minutes=10)
async def autoreact_loop():
    global auto_react_emoji
    if not auto_react_emoji:
        return  # Exit if emoji is not set

    log_channel = bot.get_channel(LOG_REACT_ID)

    for channel_id in REACT_CHANNEL_IDS:
        channel = bot.get_channel(channel_id)
        if not channel:
            if log_channel:
                await log_channel.send(f"⚠️ Could not find channel with ID {channel_id}.")
            continue

        try:
            messages = [msg async for msg in channel.history(limit=100) if not msg.author.bot]
            if not messages:
                continue

            message_to_react = random.choice(messages)
            await message_to_react.add_reaction(auto_react_emoji)

            if log_channel:
                message_link = f"https://discord.com/channels/{channel.guild.id}/{channel.id}/{message_to_react.id}"
                await log_channel.send(
                    f"✅ Auto-reacted with {auto_react_emoji} in {channel.mention} of **{channel.guild.name}**.\n[Jump to message]({message_link})"
                )
        except Exception as e:
            if log_channel:
                await log_channel.send(f"⚠️ Error while reacting in {channel.mention}: `{e}`")

# ---------------------------------------------------------------------------------------------------

LOG_DM_CHANNEL_ID = 1364839238960549908  # <- your log channel ID

@bot.command(name="dm")
@commands.has_permissions(administrator=True)
async def dm(ctx, target: str, *, message: str):
    log_channel = ctx.guild.get_channel(LOG_DM_CHANNEL_ID)
    if not log_channel:
        await ctx.send("❌ Log channel not found.")
        return

    member = None
    try:
        if target.startswith("<@") and target.endswith(">"):
            user_id = int(target.strip("<@!>"))
            member = await ctx.guild.fetch_member(user_id)
        else:
            user_id = int(target)
            member = await ctx.guild.fetch_member(user_id)
    except:
        pass

    role = None
    if not member:
        if target.startswith("<@&") and target.endswith(">"):
            try:
                role_id = int(target.strip("<@&>"))
                role = ctx.guild.get_role(role_id)
            except:
                pass
        else:
            role = discord.utils.find(lambda r: r.name.lower() == target.lower(), ctx.guild.roles)

    if member:
        try:
            await member.send(message)
            await ctx.send(f"📩 Message sent to {member.mention}")
            await log_channel.send(f"✅ DM sent to {member.mention} by {ctx.author.mention}\n**Message:** {message}")
        except discord.Forbidden:
            await ctx.send(f"❌ Couldn't DM {member.mention}.")
            await log_channel.send(f"❌ Failed to DM {member.mention} (DMs closed?) by {ctx.author.mention}")
    elif role:
        sent = 0
        failed = 0
        await ctx.send(f"⏳ Sending message to `{role.name}`... This may take a while.")

        for member in role.members:
            if member.bot:
                continue
            try:
                await member.send(message)
                sent += 1
                await log_channel.send(f"✅ DM sent to {member.mention} (role: {role.name})")
            except discord.Forbidden:
                failed += 1
                await log_channel.send(f"❌ Failed to DM {member.mention} (role: {role.name})")
            await asyncio.sleep(1.5)  # Delay to prevent rate limits

        await ctx.send(f"✅ Done! Sent to {sent} users. ❌ Failed for {failed}.")
        await log_channel.send(f"📊 Finished DM to role `{role.name}` — ✅ {sent}, ❌ {failed}")
    else:
        await ctx.send("❌ Could not find user or role. Use a valid mention, name, or ID.")

# --------------------------------------------------------------------------------------

EXCLUDED_VC_IDS = [1359117693546139731, 1351065423327531079, 1361743840918245416, 1359930327048654858, 1360687436841357495, 1360687666357735626, 1360688112744927382, 1360688267846090762, 1365046089220358244]  # Replace with your private VC channel IDs

@bot.command(name="randomvc")
async def random_vc(ctx):
    if not ctx.author.voice:
        await ctx.send("❌ You must be connected to a voice channel to use this command.")
        return

    # Include channels with no members (empty channels)
    voice_channels = [
        ch for ch in ctx.guild.voice_channels
        if ch.id not in EXCLUDED_VC_IDS and ch != ctx.author.voice.channel
        and ch.permissions_for(ctx.guild.me).connect  # Check if the bot can connect
        and ch.permissions_for(ctx.guild.me).speak  # Check if the bot can speak
        and (ch.user_limit == 0 or len(ch.members) < ch.user_limit)  # Check if user limit is not exceeded
    ]
    
    if not voice_channels:
        await ctx.send("⚠️ No available voice channels found to join (excluding private, locked, or full ones).")
        return

    target_channel = random.choice(voice_channels)

    # Debug: Show the available channels
    print(f"Available voice channels: {[ch.name for ch in voice_channels]}")

    try:
        await ctx.author.move_to(target_channel)
        await ctx.send(f"🔀 Moved you to `{target_channel.name}`!")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to move you.")
    except discord.HTTPException:
        await ctx.send("⚠️ Something went wrong while moving you.")
# -------------------------------------------------------------------------------

@bot.command(name="np")
async def now_playing(ctx):
    # Check if the author has Spotify activity (it will show in the presence of the user)
    for activity in ctx.author.activities:
        if isinstance(activity, discord.Spotify):
            track_name = activity.title
            artist_name = ", ".join(activity.artists)
            album_name = activity.album
            album_cover_url = activity.album_cover_url

            embed = discord.Embed(
                title="🎶 Now Playing",
                description=f"**{track_name}**\nby {artist_name}\nAlbum: {album_name}",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=album_cover_url)
            await ctx.send(embed=embed)
            return
    
    await ctx.send("❌ You are not currently playing any music on Spotify.")

# -----------------------------------------------------------------------------------

@bot.command(name="sms")
async def sms(ctx, user_id: int, *, message: str):
    try:
        # Check if the user is in the server
        user = discord.utils.get(ctx.guild.members, id=user_id)
        
        if user:
            # If the user is in the server, send them a DM
            await user.send(message)
            await ctx.send(f"✅ Message sent to {user.name}!")
        else:
            # If the user is not in the server, attempt to DM using the provided user ID
            user = await bot.fetch_user(user_id)
            await user.send(message)
            await ctx.send(f"✅ Message sent to {user.name} (outside the server)!")

    except discord.DiscordException as e:
        await ctx.send(f"❌ Failed to send the message: {e}")
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {e}")

# ---------------------------------------------------------------------------------

@bot.command()
async def join(ctx):
    # Check if the user is in a voice channel
    if ctx.author.voice:
        # Get the voice channel the user is in
        channel = ctx.author.voice.channel
        # Connect to the voice channel
        await channel.connect()
        await ctx.send(f"Joined {channel.name} and staying here.")
    else:
        await ctx.send("You are not connected to a voice channel.")

@bot.command()
async def leave(ctx):
    # Get the bot's voice client
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client:
        # Disconnect the bot from the voice channel
        await voice_client.disconnect()
        await ctx.send("Left the voice channel.")
    else:
        await ctx.send("I am not in any voice channel.")

# --------------------------------------------------------------------------

@bot.command()
@commands.has_permissions(manage_messages=True)
async def chat(ctx, channel: discord.TextChannel, *, message: str):
    try:
        await channel.send(message)
        await ctx.send(f"Message sent to {channel.mention}!")
    except discord.Forbidden:
        await ctx.send("I don't have permission to send messages in that channel.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@chat.error
async def chat_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Only staff members with **Manage Messages** permission can use this command.")

# -------------------------------

@bot.command()
async def banner(ctx, user_input=None):
    try:
        if user_input is None:
            user = ctx.author
        else:
            try:
                # Try to get user by mention or ID
                user_id = int(user_input.strip("<@!>"))
                user = await bot.fetch_user(user_id)
            except:
                return await ctx.send("Invalid user mention or ID.")

        user = await bot.fetch_user(user.id)  # Ensure full object for banner
        if user.banner:
            banner_url = user.banner.url
            embed = discord.Embed(
                title=f"{user.name}'s Banner",
                color=discord.Color.blue()
            )
            embed.set_image(url=banner_url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{user.name} has no banner set.")

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

# -----------------------------------

@bot.command()
async def tiktok(ctx, url: str):
    await ctx.send("Downloading video...")

    try:
        api_url = f"https://tikwm.com/api/?url={url}"
        res = requests.get(api_url).json()

        video_url = res["data"]["play"]
        title = res["data"].get("title", "TikTok Video")

        # Download the video as bytes
        video_response = requests.get(video_url)
        video_bytes = io.BytesIO(video_response.content)

        # Send the video directly to Discord
        await ctx.send(content=f"**{title}**", file=discord.File(video_bytes, filename="tiktok.mp4"))

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

# ---------------------------------

@bot.command()
async def serverbanner(ctx):
    if ctx.guild.banner:
        await ctx.send(f"{ctx.guild.name}'s banner:\n{ctx.guild.banner.url}")
    else:
        await ctx.send("This server doesn't have a banner set.")

@bot.command()
async def serveravatar(ctx):
    if ctx.guild.icon:
        await ctx.send(f"{ctx.guild.name}'s avatar:\n{ctx.guild.icon.url}")
    else:
        await ctx.send("This server doesn't have an avatar set.")

# ------------------------------------

TICKET_COMMAND_CHANNEL_ID = 1361757195686907925  # Replace with your actual full channel ID
SUPPORT_CATEGORY_ID = 1343219140864901150  # Replace with your real SUPPORT category ID
STAFF_ROLE_NAME = "Moderator"

open_tickets = {}

@bot.command()
async def ticket(ctx):
    if ctx.channel.id != TICKET_COMMAND_CHANNEL_ID:
        await ctx.send("You can only use this command in the ticket channel.", delete_after=5)
        return

    embed = discord.Embed(
        title="Need Support?",
        description="Click the button below to open a **private ticket** with our staff.\nWe're here to help you!",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else discord.Embed.Empty)
    embed.set_footer(text="Ticket System by YourBotName")

    create_button = Button(label="🎫 Open Ticket", style=discord.ButtonStyle.green)

    async def create_ticket_callback(interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild

        if user.id in open_tickets:
            await interaction.response.send_message("You already have an open ticket.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        category = guild.get_channel(SUPPORT_CATEGORY_ID)
        if category is None or not isinstance(category, discord.CategoryChannel):
            category = await guild.create_category("Tickets")

        channel_name = f"ticket-{user.name}".replace(" ", "-").lower()
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            category=category,
            reason="Ticket created"
        )

        open_tickets[user.id] = ticket_channel.id

        # Close button
        close_button = Button(label="🔒 Close Ticket", style=discord.ButtonStyle.red)

        async def close_ticket_callback(close_interaction: discord.Interaction):
            if close_interaction.user != user and STAFF_ROLE_NAME not in [role.name for role in close_interaction.user.roles]:
                await close_interaction.response.send_message("Only the ticket owner or staff can close this ticket.", ephemeral=True)
                return

            await ticket_channel.send("Closing this ticket...")
            await ticket_channel.delete()
            open_tickets.pop(user.id, None)

        close_button.callback = close_ticket_callback
        close_view = View()
        close_view.add_item(close_button)

        await ticket_channel.send(f"{user.mention}, your ticket has been created. A staff member will assist you shortly.", view=close_view)
        await interaction.response.send_message(f"Ticket created: {ticket_channel.mention}", ephemeral=True)

    create_button.callback = create_ticket_callback
    view = View()
    view.add_item(create_button)

    await ctx.send(embed=embed, view=view)

keep_alive()
bot.run(TOKEN)
