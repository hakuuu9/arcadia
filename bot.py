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
    member = after  # Corrected line

    if member.bot:
        return

    # Check the current custom status
    activities = after.activities
    custom_status = next((a for a in activities if a.type == discord.ActivityType.custom), None)
    custom_state = custom_status.state if custom_status else ""

    # Check if the member has the role
    has_role = discord.utils.get(member.roles, id=ROLE_ID)

    if INVITE_LINK in (custom_state or ""):
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

# Keep the bot alive
keep_alive()

# Run the bot using your token from environment variables
bot.run(os.getenv("BOT_TOKEN"))
