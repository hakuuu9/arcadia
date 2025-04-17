import discord
from discord.ext import commands
import asyncio
import re

class RemindCog(commands.Cog):
    """Cog for reminder related commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def remind(self, ctx, time: str, *, message: str):
        """Sets a reminder with a specified time."""
        # Match time format like 1s, 5m, 1h, 2d
        time_pattern = r"(\d+)(s|m|h|d)"
        match = re.fullmatch(time_pattern, time.lower())

        if not match:
            await ctx.send("Invalid time format. Use formats like `10s`, `5m`, `1h`, or `2d`.")
            return

        amount, unit = int(match.group(1)), match.group(2)
        seconds = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
        wait_time = amount * seconds

        # Confirm the reminder to the user
        await ctx.send(f"⏰ I’ll remind you in **{time}** about: {message}")
        
        # Wait for the specified time before sending the reminder
        await asyncio.sleep(wait_time)

        # Send the reminder to the user
        await ctx.send(f"🔔 <@{ctx.author.id}> Reminder: {message}")

def setup(bot):
    bot.add_cog(RemindCog(bot))
    
