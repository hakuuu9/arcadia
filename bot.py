from config import ROLE_ID, INVITE_LINK, BOT_TOKEN
from keep_alive import keep_alive
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

@bot.event
async def on_presence_update(before, after):
    if after.activity and INVITE_LINK in str(after.activity.name):
        guild = after.guild
        role = guild.get_role(ROLE_ID)
        if role and role not in after.roles:
            await after.add_roles(role)
            print(f"✅ Gave {after} the role for using the vanity link!")

keep_alive()
bot.run(BOT_TOKEN)
