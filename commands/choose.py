from discord.ext import commands
import random

class Choose(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def choose(self, ctx, *, choices):
        options = [option.strip() for option in choices.split(",") if option.strip()]
        if len(options) < 2:
            await ctx.send("Please provide at least two options separated by commas.")
        else:
            choice = random.choice(options)
            await ctx.send(f"I choose: **{choice}**")

def setup(bot):
    bot.add_cog(Choose(bot))
  
