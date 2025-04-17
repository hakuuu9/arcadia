import discord
from discord.ext import commands
import random

class Ship(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member):
        percent = random.randint(0, 100)
        hearts = "❤️" * (percent // 20) or "💔"
        nicknames = ["Lovebirds", "Twin Flames", "Sweethearts", "Power Couple", "Perfect Pair"]
        description = f"**{user1.display_name}** 💞 **{user2.display_name}**\nCompatibility: **{percent}%** {hearts}"
        
        if percent >= 50:
            description += f"\nCouple Nickname: **{random.choice(nicknames)}**"
        
        await ctx.send(description)

# Setup the cog
def setup(bot):
    bot.add_cog(Ship(bot))
    
