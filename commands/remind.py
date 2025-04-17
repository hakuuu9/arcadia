import re
import asyncio
from discord.ext import commands
from discord.ext.commands import Context

class Remind(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def remind(self, ctx: Context, time: str, *, message: str):
        time_pattern = r"(\d+)(s|m|h|d)"
        match = re.fullmatch(time_pattern, time.lower())
        if not match:
            await ctx.send("Invalid time format. Use formats like `10s`, `5m`, `1h`, or `2d`.")
            return

        amount, unit = int(match.group(1)), match.group(2)
        seconds = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
        wait_time = amount * seconds

        await ctx.send(f"⏰ I’ll remind you in **{time}** about: {message}")
        await asyncio.sleep(wait_time)
        await ctx.send(f"🔔 <@{ctx.author.id}> Reminder: {message}")

def setup(bot):
    bot.add_cog(Remind(bot))
  
