import discord
import datetime
from discord.ext import commands
from config import VANITY_LINK, LOG_CHANNEL_ID

class VanityMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before == after:
            return

        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return

        changes = []

        # Custom Status Change
        if before.activity != after.activity:
            before_status = before.activity.name if before.activity else "None"
            after_status = after.activity.name if after.activity else "None"
            changes.append(f"📝 **Custom Status changed**\nBefore: `{before_status}`\nAfter: `{after_status}`")

        # Bio Change & Vanity Check
        if hasattr(before, "bio") and hasattr(after, "bio") and before.bio != after.bio:
            before_bio = before.bio if before.bio else "None"
            after_bio = after.bio if after.bio else "None"
            changes.append(f"🧾 **Bio changed**\nBefore: `{before_bio}`\nAfter: `{after_bio}`")

            if VANITY_LINK in after_bio and VANITY_LINK not in before_bio:
                changes.append(f"🔗 **Vanity link added to bio!** ({VANITY_LINK})")
            elif VANITY_LINK in before_bio and VANITY_LINK not in after_bio:
                changes.append(f"❌ **Vanity link removed from bio!** ({VANITY_LINK})")

        # Send embed if changes were detected
        if changes:
            embed = discord.Embed(
                title="🔔 Member Update",
                description=f"**User:** {after.mention} (`{after}`)\n**ID:** `{after.id}`",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.utcnow()
            )
            for change in changes:
                embed.add_field(name="Update", value=change, inline=False)

            await log_channel.send(embed=embed)

def setup(bot):
    bot.add_cog(VanityMonitor(bot))
          
