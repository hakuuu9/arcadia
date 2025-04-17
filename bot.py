import discord
from discord.ext import commands
from discord import utils
import config

intents = discord.Intents.default()
intents.members = True  # We need this to track member updates (e.g., status changes)

bot = commands.Bot(command_prefix="$", intents=intents)

# Event that runs when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Check if a user's status contains a vanity link
async def check_vanity_link_in_status(user):
    for link, role_name in config.VANITY_LINKS.items():
        if link in user.activity and role_name:
            role = utils.get(user.guild.roles, name=role_name)
            if role:
                if role not in user.roles:
                    await user.add_roles(role)
                    print(f"Assigned {role_name} to {user.name}")
        else:
            # If the vanity link is not in the status, remove the role if it exists
            role = utils.get(user.guild.roles, name=role_name)
            if role and role in user.roles:
                await user.remove_roles(role)
                print(f"Removed {role_name} from {user.name}")

# Event that runs when a member's status changes
@bot.event
async def on_member_update(before, after):
    # Check if the user's status has changed
    if before.activity != after.activity:
        await check_vanity_link_in_status(after)

# Run the bot
if __name__ == "__main__":
    bot.run(config.DISCORD_TOKEN)
