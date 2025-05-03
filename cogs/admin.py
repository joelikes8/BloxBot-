import discord
from discord import app_commands
from discord.ext import commands
from database.db import get_db
from database.models import User, Order, Payment, OrderState
from utils.helpers import (
    check_if_staff, check_if_admin, update_order_status, 
    verify_payment, get_order_by_number
)
from utils.embeds import create_basic_embed
from utils.cooldowns import cooldown
from utils.constants import ADMIN_COOLDOWN, EMOJI_SUCCESS, EMOJI_ERROR, EMOJI_WARNING

class Admin(commands.Cog):
    """Admin and staff commands for managing users, orders, and payments."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="review-payment", description="Accept or reject submitted payment proof")
    @cooldown(1, ADMIN_COOLDOWN)
    @app_commands.describe(
        user="The user who submitted the payment",
        order_number="The order number",
        action="Accept or reject the payment"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Accept", value="accept"),
        app_commands.Choice(name="Reject", value="reject")
    ])
    async def review_payment(
        self, 
        interaction: discord.Interaction, 
        user: discord.User, 
        order_number: str, 
        action: app_commands.Choice[str]
    ):
        """Accept or reject submitted payment proof."""
        # Check if user is staff
        if not await check_if_staff(interaction):
            return
        
        # Get the order
        order = get_order_by_number(order_number)
        
        if not order:
            await interaction.response.send_message(
                f"{EMOJI_ERROR} Order #{order_number} not found. Please check the order number and try again.",
                ephemeral=True
            )
            return
        
        # Get the user from the database
        db = get_db()
        target_user = db.query(User).filter(User.discord_id == str(user.id)).first()
        
        if not target_user:
            await interaction.response.send_message(
                f"{EMOJI_ERROR} User not found in the database.",
                ephemeral=True
            )
            return
        
        # Check if the order belongs to the user
        if order.user_id != target_user.id:
            await interaction.response.send_message(
                f"{EMOJI_ERROR} This order does not belong to the specified user.",
                ephemeral=True
            )
            return
        
        # Check if there are any payments to review
        if not order.payments:
            await interaction.response.send_message(
                f"{EMOJI_ERROR} No payments found for this order.",
                ephemeral=True
            )
            return
        
        # Get the most recent payment
        payment = max(order.payments, key=lambda p: p.submitted_at)
        
        # Check if the payment is already verified
        if payment.is_verified:
            await interaction.response.send_message(
                f"{EMOJI_WARNING} This payment has already been verified.",
                ephemeral=True
            )
            return
        
        # Accept or reject the payment
        if action.value == "accept":
            # Verify the payment
            verify_payment(payment.id, True)
            
            # Update the order status
            update_order_status(
                order.id,
                OrderState.PAYMENT_RECEIVED,
                interaction.user.name,
                f"Payment of {payment.amount} Robux verified"
            )
            
            embed = create_basic_embed(
                f"{EMOJI_SUCCESS} Payment Accepted", 
                f"Payment for order #{order.order_number} has been accepted.",
                discord.Color.green()
            )
            
            embed.add_field(
                name="User",
                value=user.mention,
                inline=True
            )
            
            embed.add_field(
                name="Amount",
                value=f"{payment.amount} Robux",
                inline=True
            )
            
            embed.add_field(
                name="New Order Status",
                value="Payment Received",
                inline=True
            )
            
            # Try to notify the user via DM
            try:
                user_embed = create_basic_embed(
                    "💰 Payment Accepted", 
                    f"Your payment for order #{order.order_number} has been accepted!",
                    discord.Color.green()
                )
                
                user_embed.add_field(
                    name="Amount",
                    value=f"{payment.amount} Robux",
                    inline=True
                )
                
                user_embed.add_field(
                    name="Next Steps",
                    value="Development will begin on your bot soon. You'll be notified of any updates.",
                    inline=False
                )
                
                await user.send(embed=user_embed)
                embed.add_field(
                    name="User Notification",
                    value="User has been notified via DM.",
                    inline=False
                )
            except discord.Forbidden:
                embed.add_field(
                    name="User Notification",
                    value="Could not send DM to user (they may have DMs disabled).",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
        else:
            # Reject the payment
            verify_payment(payment.id, False)
            
            # Update the order status
            update_order_status(
                order.id,
                OrderState.PAYMENT_WAITING,
                interaction.user.name,
                f"Payment of {payment.amount} Robux rejected"
            )
            
            # Ask for reason
            reason_modal = ReasonModal(title="Payment Rejection Reason")
            await interaction.response.send_modal(reason_modal)
            
            # Wait for the modal to be submitted
            await reason_modal.wait()
            
            if reason_modal.reason_value:
                embed = create_basic_embed(
                    f"{EMOJI_WARNING} Payment Rejected", 
                    f"Payment for order #{order.order_number} has been rejected.",
                    discord.Color.red()
                )
                
                embed.add_field(
                    name="User",
                    value=user.mention,
                    inline=True
                )
                
                embed.add_field(
                    name="Amount",
                    value=f"{payment.amount} Robux",
                    inline=True
                )
                
                embed.add_field(
                    name="Reason",
                    value=reason_modal.reason_value,
                    inline=False
                )
                
                # Try to notify the user via DM
                try:
                    user_embed = create_basic_embed(
                        "❌ Payment Rejected", 
                        f"Your payment for order #{order.order_number} has been rejected.",
                        discord.Color.red()
                    )
                    
                    user_embed.add_field(
                        name="Amount",
                        value=f"{payment.amount} Robux",
                        inline=True
                    )
                    
                    user_embed.add_field(
                        name="Reason",
                        value=reason_modal.reason_value,
                        inline=False
                    )
                    
                    user_embed.add_field(
                        name="Next Steps",
                        value="Please submit a new payment with `/submit-payment` or contact staff for assistance.",
                        inline=False
                    )
                    
                    await user.send(embed=user_embed)
                    embed.add_field(
                        name="User Notification",
                        value="User has been notified via DM.",
                        inline=False
                    )
                except discord.Forbidden:
                    embed.add_field(
                        name="User Notification",
                        value="Could not send DM to user (they may have DMs disabled).",
                        inline=False
                    )
                
                await interaction.followup.send(embed=embed)
    
    # Modal for collecting rejection reason
    class ReasonModal(discord.ui.Modal):
        reason = discord.ui.TextInput(
            label="Reason for Rejection",
            placeholder="Explain why the payment is being rejected...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=500
        )
        
        def __init__(self, title):
            super().__init__(title=title)
            self.reason_value = None
            
        async def on_submit(self, interaction: discord.Interaction):
            self.reason_value = self.reason.value
            await interaction.response.defer()
    
    @app_commands.command(name="update-status", description="Change an order's progress stage")
    @cooldown(1, ADMIN_COOLDOWN)
    @app_commands.describe(
        order_number="The order number",
        status="The new status",
        comment="Optional comment about the status change"
    )
    @app_commands.choices(status=[
        app_commands.Choice(name="Pending", value="pending"),
        app_commands.Choice(name="Payment Waiting", value="payment_waiting"),
        app_commands.Choice(name="Payment Received", value="payment_received"),
        app_commands.Choice(name="In Progress", value="in_progress"),
        app_commands.Choice(name="Review", value="review"),
        app_commands.Choice(name="Complete", value="complete"),
        app_commands.Choice(name="Cancelled", value="cancelled"),
        app_commands.Choice(name="Rejected", value="rejected")
    ])
    async def update_status(
        self, 
        interaction: discord.Interaction, 
        order_number: str, 
        status: app_commands.Choice[str],
        comment: str = None
    ):
        """Change an order's progress stage."""
        # Check if user is staff
        if not await check_if_staff(interaction):
            return
        
        # Get the order
        order = get_order_by_number(order_number)
        
        if not order:
            await interaction.response.send_message(
                f"{EMOJI_ERROR} Order #{order_number} not found. Please check the order number and try again.",
                ephemeral=True
            )
            return
        
        # Convert string status to enum
        new_status = OrderState(status.value)
        
        # Update the order status
        if update_order_status(order.id, new_status, interaction.user.name, comment):
            embed = create_basic_embed(
                f"{EMOJI_SUCCESS} Order Status Updated", 
                f"Order #{order.order_number} has been updated to: **{new_status.name}**",
                discord.Color.green()
            )
            
            embed.add_field(
                name="Previous Status",
                value=order.status.name,
                inline=True
            )
            
            embed.add_field(
                name="New Status",
                value=new_status.name,
                inline=True
            )
            
            if comment:
                embed.add_field(
                    name="Comment",
                    value=comment,
                    inline=False
                )
            
            # Try to notify the user via DM
            try:
                # Get the discord user
                user = await self.bot.fetch_user(int(order.user.discord_id))
                
                if user:
                    user_embed = create_basic_embed(
                        "📢 Order Status Update", 
                        f"Your order #{order.order_number} has been updated!",
                        discord.Color.blue()
                    )
                    
                    user_embed.add_field(
                        name="New Status",
                        value=new_status.name,
                        inline=True
                    )
                    
                    if comment:
                        user_embed.add_field(
                            name="Comment",
                            value=comment,
                            inline=False
                        )
                    
                    user_embed.add_field(
                        name="Updated By",
                        value=interaction.user.name,
                        inline=True
                    )
                    
                    await user.send(embed=user_embed)
                    embed.add_field(
                        name="User Notification",
                        value="User has been notified via DM.",
                        inline=False
                    )
            except Exception as e:
                embed.add_field(
                    name="User Notification",
                    value=f"Could not notify user: {str(e)}",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                f"{EMOJI_ERROR} Failed to update the order status. Please try again.",
                ephemeral=True
            )
    
    @app_commands.command(name="warn", description="Issue a warning to a user")
    @cooldown(1, ADMIN_COOLDOWN)
    @app_commands.describe(
        user="The user to warn",
        reason="Reason for the warning"
    )
    async def warn(self, interaction: discord.Interaction, user: discord.User, reason: str):
        """Issue a warning to a user."""
        # Check if user is staff
        if not await check_if_staff(interaction):
            return
        
        # Get the user from the database
        db = get_db()
        target_user = db.query(User).filter(User.discord_id == str(user.id)).first()
        
        if not target_user:
            await interaction.response.send_message(
                f"{EMOJI_ERROR} User not found in the database.",
                ephemeral=True
            )
            return
        
        # Create a warning embed
        embed = create_basic_embed(
            f"{EMOJI_WARNING} User Warned", 
            f"{user.mention} has been warned.",
            discord.Color.orange()
        )
        
        embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )
        
        embed.add_field(
            name="Warned By",
            value=interaction.user.mention,
            inline=True
        )
        
        # Try to send a DM to the user
        try:
            user_embed = create_basic_embed(
                "⚠️ Warning", 
                "You have received a warning from the Roblox Bot Orders staff.",
                discord.Color.orange()
            )
            
            user_embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )
            
            user_embed.add_field(
                name="Warned By",
                value=interaction.user.name,
                inline=True
            )
            
            await user.send(embed=user_embed)
            embed.add_field(
                name="DM Status",
                value="User has been notified via DM.",
                inline=False
            )
        except discord.Forbidden:
            embed.add_field(
                name="DM Status",
                value="Could not send DM to user (they may have DMs disabled).",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="ban", description="Ban a user from the server or future orders")
    @cooldown(1, ADMIN_COOLDOWN)
    @app_commands.describe(
        user="The user to ban",
        reason="Reason for the ban",
        delete_messages="Delete recent messages from this user (days)"
    )
    async def ban(
        self, 
        interaction: discord.Interaction, 
        user: discord.User, 
        reason: str,
        delete_messages: int = 0
    ):
        """Ban a user from the server or future orders."""
        # Check if user is admin
        if not await check_if_admin(interaction):
            return
        
        # Check if delete_messages is valid
        if delete_messages < 0 or delete_messages > 7:
            await interaction.response.send_message(
                f"{EMOJI_ERROR} Delete messages value must be between 0 and 7 days.",
                ephemeral=True
            )
            return
        
        # Create a ban confirmation view
        view = BanConfirmation(interaction, user, reason, delete_messages)
        
        embed = create_basic_embed(
            "🔨 Ban Confirmation", 
            f"Are you sure you want to ban {user.mention}?",
            discord.Color.red()
        )
        
        embed.add_field(
            name="User",
            value=f"{user.name} ({user.id})",
            inline=True
        )
        
        embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )
        
        embed.add_field(
            name="Delete Messages",
            value=f"{delete_messages} days" if delete_messages > 0 else "None",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, view=view)
    
    # Confirmation view for ban command
    class BanConfirmation(discord.ui.View):
        def __init__(self, interaction, user, reason, delete_messages):
            super().__init__(timeout=60)
            self.original_interaction = interaction
            self.user = user
            self.reason = reason
            self.delete_messages = delete_messages
        
        @discord.ui.button(label="Confirm Ban", style=discord.ButtonStyle.danger)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            # Check if the user who clicked is the same as who initiated
            if interaction.user.id != self.original_interaction.user.id:
                await interaction.response.send_message(
                    f"{EMOJI_ERROR} Only the command initiator can confirm this action.",
                    ephemeral=True
                )
                return
            
            # Try to ban the user
            try:
                # Send a DM to the user before banning
                try:
                    ban_dm = create_basic_embed(
                        "🔨 You Have Been Banned", 
                        f"You have been banned from the Roblox Bot Orders server.",
                        discord.Color.red()
                    )
                    
                    ban_dm.add_field(
                        name="Reason",
                        value=self.reason,
                        inline=False
                    )
                    
                    await self.user.send(embed=ban_dm)
                except discord.Forbidden:
                    pass  # User has DMs disabled
                
                # Ban the user
                await interaction.guild.ban(
                    self.user, 
                    reason=self.reason,
                    delete_message_days=self.delete_messages
                )
                
                embed = create_basic_embed(
                    f"{EMOJI_SUCCESS} User Banned", 
                    f"{self.user.mention} has been banned from the server.",
                    discord.Color.red()
                )
                
                embed.add_field(
                    name="Reason",
                    value=self.reason,
                    inline=False
                )
                
                embed.add_field(
                    name="Banned By",
                    value=interaction.user.mention,
                    inline=True
                )
                
                embed.add_field(
                    name="Deleted Messages",
                    value=f"{self.delete_messages} days" if self.delete_messages > 0 else "None",
                    inline=True
                )
                
                await interaction.response.edit_message(embed=embed, view=None)
            except discord.Forbidden:
                await interaction.response.send_message(
                    f"{EMOJI_ERROR} I don't have permission to ban this user.",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"{EMOJI_ERROR} Failed to ban user: {str(e)}",
                    ephemeral=True
                )
        
        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            # Check if the user who clicked is the same as who initiated
            if interaction.user.id != self.original_interaction.user.id:
                await interaction.response.send_message(
                    f"{EMOJI_ERROR} Only the command initiator can cancel this action.",
                    ephemeral=True
                )
                return
            
            embed = create_basic_embed(
                "Ban Cancelled", 
                f"The ban for {self.user.mention} has been cancelled.",
                discord.Color.grey()
            )
            
            await interaction.response.edit_message(embed=embed, view=None)
    
    @app_commands.command(name="kick", description="Remove a user from the server")
    @cooldown(1, ADMIN_COOLDOWN)
    @app_commands.describe(
        user="The user to kick",
        reason="Reason for the kick"
    )
    async def kick(self, interaction: discord.Interaction, user: discord.User, reason: str):
        """Remove a user from the server."""
        # Check if user is staff
        if not await check_if_staff(interaction):
            return
        
        # Create a kick confirmation view
        view = KickConfirmation(interaction, user, reason)
        
        embed = create_basic_embed(
            "👢 Kick Confirmation", 
            f"Are you sure you want to kick {user.mention}?",
            discord.Color.orange()
        )
        
        embed.add_field(
            name="User",
            value=f"{user.name} ({user.id})",
            inline=True
        )
        
        embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, view=view)
    
    # Confirmation view for kick command
    class KickConfirmation(discord.ui.View):
        def __init__(self, interaction, user, reason):
            super().__init__(timeout=60)
            self.original_interaction = interaction
            self.user = user
            self.reason = reason
        
        @discord.ui.button(label="Confirm Kick", style=discord.ButtonStyle.danger)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            # Check if the user who clicked is the same as who initiated
            if interaction.user.id != self.original_interaction.user.id:
                await interaction.response.send_message(
                    f"{EMOJI_ERROR} Only the command initiator can confirm this action.",
                    ephemeral=True
                )
                return
            
            # Try to kick the user
            try:
                # Send a DM to the user before kicking
                try:
                    kick_dm = create_basic_embed(
                        "👢 You Have Been Kicked", 
                        f"You have been kicked from the Roblox Bot Orders server.",
                        discord.Color.orange()
                    )
                    
                    kick_dm.add_field(
                        name="Reason",
                        value=self.reason,
                        inline=False
                    )
                    
                    await self.user.send(embed=kick_dm)
                except discord.Forbidden:
                    pass  # User has DMs disabled
                
                # Kick the user
                await interaction.guild.kick(
                    self.user, 
                    reason=self.reason
                )
                
                embed = create_basic_embed(
                    f"{EMOJI_SUCCESS} User Kicked", 
                    f"{self.user.mention} has been kicked from the server.",
                    discord.Color.orange()
                )
                
                embed.add_field(
                    name="Reason",
                    value=self.reason,
                    inline=False
                )
                
                embed.add_field(
                    name="Kicked By",
                    value=interaction.user.mention,
                    inline=True
                )
                
                await interaction.response.edit_message(embed=embed, view=None)
            except discord.Forbidden:
                await interaction.response.send_message(
                    f"{EMOJI_ERROR} I don't have permission to kick this user.",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"{EMOJI_ERROR} Failed to kick user: {str(e)}",
                    ephemeral=True
                )
        
        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            # Check if the user who clicked is the same as who initiated
            if interaction.user.id != self.original_interaction.user.id:
                await interaction.response.send_message(
                    f"{EMOJI_ERROR} Only the command initiator can cancel this action.",
                    ephemeral=True
                )
                return
            
            embed = create_basic_embed(
                "Kick Cancelled", 
                f"The kick for {self.user.mention} has been cancelled.",
                discord.Color.grey()
            )
            
            await interaction.response.edit_message(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(Admin(bot))
