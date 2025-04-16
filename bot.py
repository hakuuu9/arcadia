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
    print(f"{bot.user.name} is online and monitoring status and bio.")

@bot.event
async def on_presence_update(before, after):
    member = after
    if member.bot:
        return

    # Check custom status
    activities = member.activities
    custom_status = next((a for a in activities if a.type == discord.ActivityType.custom), None)
    custom_state = custom_status.state if custom_status else ""

    has_role = discord.utils.get(member.roles, id=ROLE_ID)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    # Check bio
    try:
        full_user = await bot.fetch_user(member.id)
        bio = full_user.bio or ""
    except Exception as e:
        print(f"Error fetching bio: {e}")
        bio = ""

    # Conditions
    link_in_status = INVITE_LINK in (custom_state or "")
    link_in_bio = INVITE_LINK in bio

    if link_in_status or link_in_bio:
        if not has_role:
            try:
                await member.add_roles(discord.Object(id=ROLE_ID))
                print(f"✅ Added role to {member.display_name} (status/bio)")
                if log_channel:
                    await log_channel.send(f"✅ Added role to `{member.display_name}` (used vanity link).")
            except Exception as e:
                print(f"Error adding role: {e}")
    else:
        if has_role:
            try:
                await member.remove_roles(discord.Object(id=ROLE_ID))
                print(f"❌ Removed role from {member.display_name} (status/bio)")
                if log_channel:
                    await log_channel.send(f"❌ Removed role from `{member.display_name}` (removed vanity link).")
            except Exception as e:
                print(f"Error removing role: {e}")

keep_alive()
bot.run(os.getenv("BOT_TOKEN"))
