import discord
from discord.ext import commands
from config import ROLE_ID, INVITE_LINK, BOT_TOKEN
from keep_alive import keep_alive  # Import the keep-alive function

# 🔍 Intents required to detect statuses and manage roles
intents = discord.Intents.default()
intents.presences = True
intents.members = True

# 🧠 Create the bot with the specified command prefix and intents
bot = commands.Bot(command_prefix='!', intents=intents)

# 🔁 Start the keep-alive server
keep_alive()

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

@bot.event
async def on_presence_update(before, after):
    member = after

    if member.bot:
        return  # Ignore bots

    role = member.guild.get_role(ROLE_ID)
    if not role:
        print("❌ Role not found!")
        return

    if role in member.roles:
        return  # Already has the role

    # Check the user's custom status
    for activity in after.activities:
        if isinstance(activity, discord.CustomActivity):
            if activity.name and INVITE_LINK in activity.name:
                try:
                    await member.add_roles(role)
                    print(f"✅ Gave {member} the role for using the vanity link!")
                except Exception as e:
                    print(f"❌ Failed to add role: {e}")
                break

# 🔁 Start the bot
bot.run(BOT_TOKEN)
