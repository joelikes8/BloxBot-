import discord
from discord import app_commands
from discord.ext import commands
from utils.helpers import (
    check_if_registered, check_if_staff, 
    toggle_subscription, create_notification
)
from utils.embeds import create_basic_embed
from utils.constants import DEFAULT_COOLDOWN, EMOJI_SUCCESS, EMOJI_ERROR
from utils.cooldowns import cooldown
from database.db import get_db
from database.models import User, Subscription

class Notifications(commands.Cog):
    """Commands for managing notification preferences and sending notifications."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="subscribe", description="Enable notifications when your order updates or finishes")
    @cooldown(1, DEFAULT_COOLDOWN)
    @app_commands.describe(
        order_updates="Enable notifications for order status updates", 
        announcements="Enable notifications for announcements"
    )
    async def subscribe(
        self, 
        interaction: discord.Interaction, 
        order_updates: bool = True, 
        announcements: bool = True
    ):
        """Enable notifications when your order updates or finishes."""
        # Check if user is registered
        if not await check_if_registered(interaction):
            return
        
        # Update subscription preferences
        subscription = toggle_subscription(
            str(interaction.user.id),  # Convert Discord ID to string
            order_updates=order_updates,
            announcements=announcements
        )
        
        if subscription:
            embed = create_basic_embed(
                f"{EMOJI_SUCCESS} Notification Preferences Updated", 
                "Your notification preferences have been updated.",
                discord.Color.green()
            )
            
            embed.add_field(
                name="Order Updates",
                value="Enabled ✅" if subscription.order_updates else "Disabled ❌",
                inline=True
            )
            
            embed.add_field(
                name="Announcements",
                value="Enabled ✅" if subscription.announcements else "Disabled ❌",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                f"{EMOJI_ERROR} Failed to update your notification preferences. Please try again.",
                ephemeral=True
            )
    
    @app_commands.command(name="unsubscribe", description="Turn off order or announcement notifications")
    @cooldown(1, DEFAULT_COOLDOWN)
    @app_commands.describe(
        order_updates="Disable notifications for order status updates", 
        announcements="Disable notifications for announcements"
    )
    async def unsubscribe(
        self, 
        interaction: discord.Interaction, 
        order_updates: bool = True, 
        announcements: bool = True
    ):
        """Turn off order or announcement notifications."""
        # Check if user is registered
        if not await check_if_registered(interaction):
            return
        
        # Update subscription preferences by disabling specified types
        subscription = toggle_subscription(
            str(interaction.user.id),  # Convert Discord ID to string
            order_updates=not order_updates if order_updates else None,
            announcements=not announcements if announcements else None
        )
        
        if subscription:
            embed = create_basic_embed(
                f"{EMOJI_SUCCESS} Notification Preferences Updated", 
                "Your notification preferences have been updated.",
                discord.Color.green()
            )
            
            embed.add_field(
                name="Order Updates",
                value="Enabled ✅" if subscription.order_updates else "Disabled ❌",
                inline=True
            )
            
            embed.add_field(
                name="Announcements",
                value="Enabled ✅" if subscription.announcements else "Disabled ❌",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                f"{EMOJI_ERROR} Failed to update your notification preferences. Please try again.",
                ephemeral=True
            )
    
    @app_commands.command(name="notify", description="Staff command to notify users of order status")
    @cooldown(1, DEFAULT_COOLDOWN)
    @app_commands.describe(
        user="The user to notify",
        message="The notification message"
    )
    async def notify(self, interaction: discord.Interaction, user: discord.User, message: str):
        """Staff command to notify users of order status."""
        # Check if user is staff
        if not await check_if_staff(interaction):
            return
        
        # Get the target user from the database
        db = get_db()
        target_user = db.query(User).filter(User.discord_id == str(user.id)).first()
        
        if not target_user:
            await interaction.response.send_message(
                f"{EMOJI_ERROR} User not found in the database. They need to register first.",
                ephemeral=True
            )
            return
        
        # Create a notification for the user
        if await create_notification(str(user.id), message):
            embed = create_basic_embed(
                f"{EMOJI_SUCCESS} Notification Sent", 
                f"Notification sent to {user.mention}.",
                discord.Color.green()
            )
            
            embed.add_field(
                name="Message",
                value=message,
                inline=False
            )
            
            # Try to DM the user
            try:
                user_embed = create_basic_embed(
                    "📢 New Notification", 
                    "You have received a new notification.",
                    discord.Color.blue()
                )
                
                user_embed.add_field(
                    name="Message",
                    value=message,
                    inline=False
                )
                
                user_embed.add_field(
                    name="From",
                    value=interaction.user.name,
                    inline=True
                )
                
                await user.send(embed=user_embed)
                embed.add_field(
                    name="DM Status",
                    value="Direct message sent to user.",
                    inline=True
                )
            except discord.Forbidden:
                embed.add_field(
                    name="DM Status",
                    value="Could not send DM to user (they may have DMs disabled).",
                    inline=True
                )
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                f"{EMOJI_ERROR} Failed to create notification. Please try again.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Notifications(bot))
