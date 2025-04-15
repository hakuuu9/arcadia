import discord
from discord.ext import commands
from config import ROLE_ID, INVITE_LINK
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
    member = after.member or after.user

    if member.bot:
        return

    # Check the current custom status
    activities = after.activities
    custom_status = next((a for a in activities if a.type == discord.ActivityType.custom), None)
    custom_state = custom_status.state if custom_status else ""

    # Check if the role is already assigned
    has_role = discord.utils.get(member.roles, id=ROLE_ID)

    if INVITE_LINK in custom_state:
        if not has_role:
            try:
                await member.add_roles(discord.Object(id=ROLE_ID))
                print(f"✅ Added role to {member.display_name}")
            except Exception as e:
                print(f"Error adding role: {e}")
    else:
        if has_role:
            try:
                await member.remove_roles(discord.Object(id=ROLE_ID))
                print(f"❌ Removed role from {member.display_name}")
            except Exception as e:
                print(f"Error removing role: {e}")

# Keep alive for UptimeRobot
keep_alive()

# Run bot with token from environment
bot.run(os.getenv("BOT_TOKEN"))
