import discord
from discord.ext import commands
import random

class Choose(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="choose")
    async def choose(self, ctx, *, options: str):
        """
        Command that allows the bot to choose randomly from a list of options.
        Users provide a string of options separated by commas.
        Example usage: $choose option1, option2, option3
        """
        # Split the options by commas and strip any extra spaces
        options_list = [option.strip() for option in options.split(',')]

        if len(options_list) < 2:
            await ctx.send("Please provide at least two options to choose from!")
            return
        
        chosen_option = random.choice(options_list)
        await ctx.send(f"I choose: **{chosen_option}**")

# Setup the cog
def setup(bot):
    bot.add_cog(Choose(bot))
    
