import discord
from discord.ext import commands
import random

class EightBall(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="8b")
    async def eight_ball(self, ctx, *, question: str):
        responses = [
            "Absolutely yes!",
            "No doubt about it.",
            "Maybe… time will tell.",
            "I wouldn’t count on it.",
            "Ask again later.",
            "It’s a mystery even to me.",
            "Definitely not.",
            "Seems likely!",
            "Highly questionable.",
            "You already know the answer."
        ]
        response = random.choice(responses)
        await ctx.send(f"🎱 **Question:** {question}\n**Answer:** {response}")

# Setup the cog
def setup(bot):
    bot.add_cog(EightBall(bot))
    
