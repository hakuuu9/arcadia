import discord
from discord.ext import commands
from discord import utils
import config
from keep_alive import keep_alive  # Import the keep_alive function

intents = discord.Intents.default()
intents.members = True  # To track member updates (like status changes)

bot = commands.Bot(command_prefix="$", intents=intents)

# Event that runs when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Check if the user's status contains the vanity link
async def check_vanity_link_in_status(user):
    if config.VANITY_LINK in user.activity:
        # User has the vanity link in their status, so assign the role
        role = utils.get(user.guild.roles, id=config.ROLE_ID)
        if role and role not in user.roles:
            await user.add_roles(role)
            log_channel = bot.get_channel(config.LOG_CHANNEL_ID)
            await log_channel.send(f"Assigned {role.name} role to {user.name} for having the vanity link in their status.")
    else:
        # User doesn't have the vanity link in their status, remove the role
        role = utils.get(user.guild.roles, id=config.ROLE_ID)
        if role and role in user.roles:
            await user.remove_roles(role)
            log_channel = bot.get_channel(config.LOG_CHANNEL_ID)
            await log_channel.send(f"Removed {role.name} role from {user.name} for removing the vanity link from their status.")

# Event that runs when a member's status changes
@bot.event
async def on_member_update(before, after):
    if before.activity != after.activity:
        await check_vanity_link_in_status(after)

# Run the keep_alive function to ensure the bot stays alive
if __name__ == "__main__":
    keep_alive()  # Start the keep-alive server
    bot.run(config.TOKEN)  # Start the bot
