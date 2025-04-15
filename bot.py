@bot.event
async def on_presence_update(before, after):
    member = after  # ✅ Fix: after is already a Member object

    if member.bot:
        return

    # Check the current custom status
    activities = after.activities
    custom_status = next((a for a in activities if a.type == discord.ActivityType.custom), None)
    custom_state = custom_status.state if custom_status else ""

    # Check if the role is already assigned
    has_role = discord.utils.get(member.roles, id=ROLE_ID)

    if INVITE_LINK in (custom_state or ""):
        if not has_role:
            try:
                await member.add_roles(discord.Object(id=ROLE_ID))
                print(f"✅ Added role to {member.display_name}")
            except Exception as e:
                print(f"Error adding role: {e}")
    else:
        if has_role:
            try:
                await member.remove_roles(discord.Object(id=ROLE_ID))
                print(f"❌ Removed role from {member.display_name}")
            except Exception as e:
                print(f"Error removing role: {e}")
