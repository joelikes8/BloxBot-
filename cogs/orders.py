import discord
from discord import app_commands
from discord.ext import commands
import datetime
from utils.helpers import (
    check_if_registered, create_order, get_order_by_number, 
    update_order_status, create_payment
)
from utils.embeds import create_basic_embed, create_order_embed, create_pricing_embed
from utils.constants import (
    BOT_TYPES, DEFAULT_COOLDOWN, EMOJI_SUCCESS, 
    EMOJI_ERROR, EMOJI_WARNING, STATUS_DESCRIPTIONS
)
from utils.cooldowns import cooldown
from database.db import get_db
from database.models import User, Order, OrderState

class Orders(commands.Cog):
    """Commands for managing bot orders and payments."""
    
    def __init__(self, bot):
        self.bot = bot
    
    class OrderModal(discord.ui.Modal):
        """Modal for creating a new bot order."""
        
        def __init__(self):
            super().__init__(title="New Bot Order")
        
        bot_type = discord.ui.TextInput(
            label="Bot Type",
            placeholder="Choose from: " + ", ".join(BOT_TYPES),
            required=True,
            max_length=100
        )
        
        features = discord.ui.TextInput(
            label="Features (one per line)",
            style=discord.TextStyle.paragraph,
            placeholder="List the features you want (one per line)\nExample:\n- Command system\n- Currency system\n- Custom UI",
            required=True,
            max_length=1000
        )
        
        notes = discord.ui.TextInput(
            label="Additional Notes",
            style=discord.TextStyle.paragraph,
            placeholder="Any additional information or special requirements",
            required=False,
            max_length=500
        )
        
        async def on_submit(self, interaction: discord.Interaction):
            # Check if user is registered
            db = get_db()
            user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
            
            if not user:
                await interaction.response.send_message(
                    f"{EMOJI_ERROR} You are not registered! Please use `/register` first.",
                    ephemeral=True
                )
                return
            
            # Calculate approximate price based on bot type and features
            bot_type_value = self.bot_type.value
            feature_count = len(self.features.value.strip().split('\n'))
            
            base_prices = {
                "Basic Automation Bot": 500,
                "Standard Game Bot": 1000,
                "Premium Game Bot": 2500,
                "Custom Bot": 1500
            }
            
            # Calculate price based on bot type and feature count
            base_price = base_prices.get(bot_type_value, 1000)
            price = base_price + (feature_count * 100)  # Add 100 per feature
            
            # Cap prices based on bot type
            max_prices = {
                "Basic Automation Bot": 1000,
                "Standard Game Bot": 2500,
                "Premium Game Bot": 5000,
                "Custom Bot": 10000
            }
            
            if price > max_prices.get(bot_type_value, 5000):
                price = max_prices.get(bot_type_value, 5000)
            
            # Create the order
            order = create_order(
                interaction.user.id,
                bot_type_value,
                self.features.value,
                self.notes.value,
                price
            )
            
            if order:
                # Create embed to show order details
                embed = create_basic_embed(
                    f"{EMOJI_SUCCESS} Order Created", 
                    f"Your order #{order.order_number} has been created!",
                    discord.Color.green()
                )
                
                embed.add_field(
                    name="Bot Type",
                    value=bot_type_value,
                    inline=True
                )
                
                embed.add_field(
                    name="Estimated Price",
                    value=f"{price} Robux",
                    inline=True
                )
                
                embed.add_field(
                    name="Next Steps",
                    value=(
                        "1. We'll review your order and confirm the final price\n"
                        "2. Use `/submit-payment` to provide proof of Robux payment\n"
                        "3. Track your order with `/order-status`"
                    ),
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    f"{EMOJI_ERROR} Failed to create your order. Please try again or contact support.",
                    ephemeral=True
                )
    
    @app_commands.command(name="order", description="Begin a custom bot request with features, type, and notes")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def order(self, interaction: discord.Interaction):
        """Begin a custom bot request with features, type, and notes."""
        # Check if user is registered
        if not await check_if_registered(interaction):
            return
        
        # Show the order form modal
        await interaction.response.send_modal(self.OrderModal())
    
    @app_commands.command(name="order-status", description="Check the live status of your bot request")
    @cooldown(1, DEFAULT_COOLDOWN)
    @app_commands.describe(order_number="The order number (e.g., ABC-1234)")
    async def order_status(self, interaction: discord.Interaction, order_number: str):
        """Check the live status of your bot request."""
        # Check if user is registered
        if not await check_if_registered(interaction):
            return
        
        # Get the order
        order = get_order_by_number(order_number)
        
        if not order:
            await interaction.response.send_message(
                f"{EMOJI_ERROR} Order #{order_number} not found. Please check the order number and try again.",
                ephemeral=True
            )
            return
        
        # Check if the order belongs to the user
        db = get_db()
        user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
        
        if order.user_id != user.id:
            # Check if the user is staff
            if not user.is_staff:
                await interaction.response.send_message(
                    f"{EMOJI_ERROR} You don't have permission to view this order.",
                    ephemeral=True
                )
                return
        
        # Generate order embed
        embed = create_order_embed(order)
        
        # Add status description
        status_description = STATUS_DESCRIPTIONS.get(order.status.value, "No status description available.")
        embed.add_field(
            name="Status Description",
            value=status_description,
            inline=False
        )
        
        # Add history of status changes
        if order.status_updates:
            # Sort by timestamp
            status_updates = sorted(order.status_updates, key=lambda x: x.changed_at)
            
            # Format the history
            history = "\n".join([
                f"• <t:{int(update.changed_at.timestamp())}:R>: **{update.status.name}**" +
                (f" - {update.comment}" if update.comment else "")
                for update in status_updates[-5:]  # Show only the last 5 updates
            ])
            
            if len(status_updates) > 5:
                history = f"• ... and {len(status_updates) - 5} earlier updates\n" + history
                
            embed.add_field(
                name="Status History",
                value=history,
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    class PaymentModal(discord.ui.Modal):
        """Modal for submitting payment proof."""
        
        def __init__(self):
            super().__init__(title="Submit Payment Proof")
        
        order_number = discord.ui.TextInput(
            label="Order Number",
            placeholder="Enter your order number (e.g., ABC-1234)",
            required=True,
            max_length=10
        )
        
        amount = discord.ui.TextInput(
            label="Payment Amount (Robux)",
            placeholder="Enter the amount of Robux you paid",
            required=True,
            max_length=10
        )
        
        proof_url = discord.ui.TextInput(
            label="Payment Proof URL",
            placeholder="Link to screenshot of your payment (Discord/Imgur link)",
            required=True,
            max_length=200
        )
        
        async def on_submit(self, interaction: discord.Interaction):
            # Check if the order exists
            order = get_order_by_number(self.order_number.value)
            
            if not order:
                await interaction.response.send_message(
                    f"{EMOJI_ERROR} Order #{self.order_number.value} not found. Please check the order number and try again.",
                    ephemeral=True
                )
                return
            
            # Check if the order belongs to the user
            db = get_db()
            user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
            
            if order.user_id != user.id:
                await interaction.response.send_message(
                    f"{EMOJI_ERROR} You don't have permission to submit payment for this order.",
                    ephemeral=True
                )
                return
            
            # Check if the order is in a valid state for payment
            if order.status not in [OrderState.PAYMENT_WAITING, OrderState.PENDING]:
                await interaction.response.send_message(
                    f"{EMOJI_WARNING} This order is not currently awaiting payment. Current status: {order.status.name}",
                    ephemeral=True
                )
                return
            
            # Validate amount is a number
            try:
                amount = float(self.amount.value)
                if amount <= 0:
                    raise ValueError("Amount must be positive")
            except ValueError:
                await interaction.response.send_message(
                    f"{EMOJI_ERROR} Invalid amount. Please enter a valid number of Robux.",
                    ephemeral=True
                )
                return
            
            # Create the payment record
            payment = create_payment(
                interaction.user.id,
                order.id,
                amount,
                self.proof_url.value
            )
            
            if payment:
                # Update order status to payment_received but needs verification
                update_order_status(
                    order.id,
                    OrderState.PAYMENT_WAITING,
                    interaction.user.name,
                    f"Payment of {amount} Robux submitted - awaiting verification"
                )
                
                # Notify staff about the new payment submission
                # This would normally be done through a notification to staff channel
                
                embed = create_basic_embed(
                    f"{EMOJI_SUCCESS} Payment Submitted", 
                    f"Your payment for order #{order.order_number} has been submitted!",
                    discord.Color.green()
                )
                
                embed.add_field(
                    name="Amount",
                    value=f"{amount} Robux",
                    inline=True
                )
                
                embed.add_field(
                    name="Status",
                    value="Awaiting Verification",
                    inline=True
                )
                
                embed.add_field(
                    name="Next Steps",
                    value=(
                        "1. Our staff will verify your payment\n"
                        "2. You'll be notified when your payment is verified\n"
                        "3. Development will begin after verification"
                    ),
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    f"{EMOJI_ERROR} Failed to submit your payment. Please try again or contact support.",
                    ephemeral=True
                )
    
    @app_commands.command(name="submit-payment", description="Upload a screenshot as proof of Robux payment")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def submit_payment(self, interaction: discord.Interaction):
        """Upload a screenshot as proof of Robux payment."""
        # Check if user is registered
        if not await check_if_registered(interaction):
            return
        
        # Show the payment submission modal
        await interaction.response.send_modal(self.PaymentModal())
    
    @app_commands.command(name="cancel-order", description="Cancel your order (if work hasn't started)")
    @cooldown(1, DEFAULT_COOLDOWN)
    @app_commands.describe(order_number="The order number (e.g., ABC-1234)")
    @app_commands.describe(reason="Reason for cancellation")
    async def cancel_order(self, interaction: discord.Interaction, order_number: str, reason: str = None):
        """Cancel your order (if work hasn't started)."""
        # Check if user is registered
        if not await check_if_registered(interaction):
            return
        
        # Get the order
        order = get_order_by_number(order_number)
        
        if not order:
            await interaction.response.send_message(
                f"{EMOJI_ERROR} Order #{order_number} not found. Please check the order number and try again.",
                ephemeral=True
            )
            return
        
        # Check if the order belongs to the user
        db = get_db()
        user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
        
        if order.user_id != user.id:
            # Check if the user is staff
            if not user.is_staff:
                await interaction.response.send_message(
                    f"{EMOJI_ERROR} You don't have permission to cancel this order.",
                    ephemeral=True
                )
                return
        
        # Check if the order can be cancelled
        if order.status in [OrderState.COMPLETE, OrderState.CANCELLED, OrderState.REJECTED]:
            await interaction.response.send_message(
                f"{EMOJI_ERROR} This order cannot be cancelled because its status is {order.status.name}.",
                ephemeral=True
            )
            return
        
        # Check if work has started
        if order.status in [OrderState.IN_PROGRESS, OrderState.REVIEW]:
            await interaction.response.send_message(
                f"{EMOJI_WARNING} This order cannot be cancelled because work has already started. Please contact staff for assistance.",
                ephemeral=True
            )
            return
        
        # Update the order status to cancelled
        update_order_status(
            order.id,
            OrderState.CANCELLED,
            interaction.user.name,
            f"Cancelled by user" + (f": {reason}" if reason else "")
        )
        
        embed = create_basic_embed(
            f"{EMOJI_SUCCESS} Order Cancelled", 
            f"Your order #{order.order_number} has been cancelled.",
            discord.Color.orange()
        )
        
        if reason:
            embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )
        
        embed.add_field(
            name="Need Help?",
            value="If you have any questions or want to place a new order, use `/support` to contact our staff.",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="pricing", description="View a detailed pricing table for all bot services")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def pricing(self, interaction: discord.Interaction):
        """View a detailed pricing table for all bot services."""
        embed = create_pricing_embed()
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Orders(bot))
