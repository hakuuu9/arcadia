import discord
from discord.ext import commands
from config import ROLE_ID, INVITE_LINK, LOG_CHANNEL_ID
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user.name} is online and monitoring presence statuses!")

@bot.event
async def on_presence_update(before, after):
    member = after  # after is already a Member object

    if member.bot:
        return

    # Check the custom status
    activities = after.activities
    custom_status = next((a for a in activities if a.type == discord.ActivityType.custom), None)
    custom_state = custom_status.state if custom_status else ""

    # Check if the member has the target role
    has_role = discord.utils.get(member.roles, id=ROLE_ID)

    # Get the log channel
    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    # If the user has the vanity link in their custom status
    if INVITE_LINK in (custom_state or ""):
        if not has_role:
            try:
                await member.add_roles(discord.Object(id=ROLE_ID))
                print(f"✅ Added role to {member.display_name}")
                if log_channel:
                    await log_channel.send(f"✅ Added role to `{member.display_name}` for using the vanity link.")
            except Exception as e:
                print(f"Error adding role: {e}")
    else:
        if has_role:
            try:
                await member.remove_roles(discord.Object(id=ROLE_ID))
                print(f"❌ Removed role from {member.display_name}")
                if log_channel:
                    await log_channel.send(f"❌ Removed role from `{member.display_name}` for removing the vanity link.")
            except Exception as e:
                print(f"Error removing role: {e}")

# Start the keep-alive server (for UptimeRobot if hosted)
keep_alive()

# Run the bot using token from environment variables
bot.run(os.getenv("BOT_TOKEN"))
