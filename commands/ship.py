import discord
from discord.ext import commands
import random

class Ship(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ship")
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member):
        percent = random.randint(1, 100)
        if percent >= 50:
            nicknames = ["TortolBabies", "CutieDuo", "SoulMatch", "LoveyPair", "Sweethearts"]
            nickname = random.choice(nicknames)
            hearts = "❤️" * (percent // 10)
            await ctx.send(f"{user1.mention} 💞 {user2.mention}\n**{percent}%** compatibility {hearts}\nCouple nickname: **{nickname}**")
        else:
            await ctx.send(f"{user1.mention} 💔 {user2.mention}\n**{percent}%** compatibility... baka friends lang talaga kayo.")

async def setup(bot):
    await bot.add_cog(Ship(bot))
