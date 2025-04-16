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
    print(f"{bot.user.name} is online and monitoring presence and bios.")

@bot.event
async def on_presence_update(before, after):
    member = after
    if member.bot:
        return

    activities = after.activities
    custom_status = next((a for a in activities if a.type == discord.ActivityType.custom), None)
    custom_state = custom_status.state if custom_status else ""

    has_role = discord.utils.get(member.roles, id=ROLE_ID)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    if INVITE_LINK in (custom_state or ""):
        if not has_role:
            try:
                await member.add_roles(discord.Object(id=ROLE_ID))
                print(f"✅ Added role to {member.display_name} (status)")
                if log_channel:
                    await log_channel.send(f"✅ Added role to `{member.display_name}` (used link in status).")
            except Exception as e:
                print(f"Error adding role: {e}")
    else:
        if has_role:
            try:
                bio = member.bio or ""
            except AttributeError:
                bio = ""

            if INVITE_LINK not in bio:
                try:
                    await member.remove_roles(discord.Object(id=ROLE_ID))
                    print(f"❌ Removed role from {member.display_name} (status)")
                    if log_channel:
                        await log_channel.send(f"❌ Removed role from `{member.display_name}` (removed link from status).")
                except Exception as e:
                    print(f"Error removing role: {e}")

@bot.event
async def on_user_update(before, after):
    if after.bot:
        return

    try:
        bio = after.bio or ""
    except AttributeError:
        return

    for guild in bot.guilds:
        member = guild.get_member(after.id)
        if not member:
            continue

        has_role = discord.utils.get(member.roles, id=ROLE_ID)
        log_channel = bot.get_channel(LOG_CHANNEL_ID)

        if INVITE_LINK in bio:
            if not has_role:
                try:
                    await member.add_roles(discord.Object(id=ROLE_ID))
                    print(f"✅ Added role to {member.display_name} (bio)")
                    if log_channel:
                        await log_channel.send(f"✅ Added role to `{member.display_name}` (used link in bio).")
                except Exception as e:
                    print(f"Error adding role from bio: {e}")
        else:
            activities = member.activities
            custom_status = next((a for a in activities if a.type == discord.ActivityType.custom), None)
            custom_state = custom_status.state if custom_status else ""

            if INVITE_LINK not in (custom_state or "") and has_role:
                try:
                    await member.remove_roles(discord.Object(id=ROLE_ID))
                    print(f"❌ Removed role from {member.display_name} (bio)")
                    if log_channel:
                        await log_channel.send(f"❌ Removed role from `{member.display_name}` (removed link from bio).")
                except Exception as e:
                    print(f"Error removing role from bio: {e}")

keep_alive()
bot.run(os.getenv("BOT_TOKEN"))
                    
