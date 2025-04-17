import discord
from discord.ext import commands
from config import VANITY_LINK
import datetime

class VanityLinkCog(commands.Cog):
    """Cog to manage vanity link related commands and logging."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def vanity(self, ctx, action: str, link: str = None):
        """Command to add or remove vanity link from user's bio."""
        if action.lower() == "add":
            if link:
                # Assuming you want to set the bio with a vanity link.
                await ctx.author.edit(bio=link)
                await ctx.send(f"🔗 Vanity link added to your bio: {link}")
            else:
                await ctx.send("Please provide the link to add.")
        elif action.lower() == "remove":
            # Removing the vanity link by clearing bio or setting to empty.
            await ctx.author.edit(bio="")
            await ctx.send("❌ Vanity link removed from your bio.")
        else:
            await ctx.send("Invalid action! Use `add <link>` to add and `remove` to remove.")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        log_channel = self.bot.get_channel(123456789012345678)  # Replace with your log channel ID
        if not log_channel:
            return

        changes = []

        if hasattr(before, "bio") and hasattr(after, "bio") and before.bio != after.bio:
            before_bio = before.bio if before.bio else "None"
            after_bio = after.bio if after.bio else "None"
            changes.append(f"🧾 **Bio changed**\nBefore: `{before_bio}`\nAfter: `{after_bio}`")

            if VANITY_LINK in after_bio and VANITY_LINK not in before_bio:
                changes.append(f"🔗 **Vanity link added to bio!** ({VANITY_LINK})")
            elif VANITY_LINK in before_bio and VANITY_LINK not in after_bio:
                changes.append(f"❌ **Vanity link removed from bio!** ({VANITY_LINK})")

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
    bot.add_cog(VanityLinkCog(bot))
            
