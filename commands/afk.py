import discord
from discord.ext import commands
from discord.ext.commands import Context

afk_users = {}

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def afk(self, ctx: Context, *, reason="AFK"):
        """Sets the user as AFK"""
        afk_users[ctx.author.id] = reason
        await ctx.send(f"🛑 {ctx.author.display_name} is now AFK: {reason}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # AFK return check
        if message.author.id in afk_users:
            del afk_users[message.author.id]
            await message.channel.send(f"👋 Welcome back, {message.author.mention}! I removed your AFK.")

        # Ping AFK user check
        for user_id in afk_users:
            if f"<@{user_id}>" in message.content:
                reason = afk_users[user_id]
                await message.channel.send(f"💤 That user is AFK: {reason}")
                break


def setup(bot):
    bot.add_cog(AFK(bot))
