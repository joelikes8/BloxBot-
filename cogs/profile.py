import discord
from discord import app_commands
from discord.ext import commands
from utils.helpers import get_or_create_user, check_if_registered, get_user_orders
from utils.embeds import create_basic_embed, create_profile_embed
from database.db import get_db
from database.models import User, Payment
from utils.constants import DEFAULT_COOLDOWN, EMOJI_SUCCESS, EMOJI_ERROR
from utils.cooldowns import cooldown

class Profile(commands.Cog):
    """Commands for managing user profiles and viewing order history."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="profile", description="View your user profile, linked Roblox name, and total orders")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def profile(self, interaction: discord.Interaction):
        """View your user profile, linked Roblox name, and total orders."""
        # Check if user is registered
        db = get_db()
        user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
        
        if not user:
            embed = create_basic_embed(
                f"{EMOJI_ERROR} Not Registered", 
                "You haven't registered yet! Use `/register` to create your profile.",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Generate profile embed
        embed = create_profile_embed(user, interaction.user)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="register", description="Register as a new customer and create your profile")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def register(self, interaction: discord.Interaction):
        """Register as a new customer and create your profile."""
        db = get_db()
        existing_user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
        
        if existing_user:
            embed = create_basic_embed(
                f"{EMOJI_ERROR} Already Registered", 
                "You already have an account! Use `/profile` to see your information.",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create new user
        user = User(
            discord_id=str(interaction.user.id),
            discord_name=interaction.user.name
        )
        
        db.add(user)
        db.commit()
        
        embed = create_basic_embed(
            f"{EMOJI_SUCCESS} Registration Successful", 
            "Your profile has been created! Use `/set-roblox` to link your Roblox username.",
            discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="set-roblox", description="Link your Roblox username for identity verification")
    @cooldown(1, DEFAULT_COOLDOWN)
    @app_commands.describe(roblox_username="Your Roblox username")
    async def set_roblox(self, interaction: discord.Interaction, roblox_username: str):
        """Link your Roblox username for identity verification."""
        # Check if user is registered
        if not await check_if_registered(interaction):
            return
        
        # Update the user's Roblox username
        db = get_db()
        user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
        
        user.roblox_username = roblox_username
        db.commit()
        
        embed = create_basic_embed(
            f"{EMOJI_SUCCESS} Roblox Username Updated", 
            f"Your Roblox username has been set to **{roblox_username}**.",
            discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="my-orders", description="See a list of all your current and past bot orders")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def my_orders(self, interaction: discord.Interaction):
        """See a list of all your current and past bot orders."""
        # Check if user is registered
        if not await check_if_registered(interaction):
            return
        
        # Get user's orders
        orders = get_user_orders(interaction.user.id)
        
        if not orders:
            embed = create_basic_embed(
                "📦 Your Orders", 
                "You don't have any orders yet. Use `/order` to place your first order!",
                discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Create embed to display orders
        embed = create_basic_embed(
            "📦 Your Orders", 
            f"You have {len(orders)} total orders.",
            discord.Color.blue()
        )
        
        # Add active orders
        active_orders = [order for order in orders if order.status.name not in ["COMPLETE", "CANCELLED", "REJECTED"]]
        if active_orders:
            active_order_list = "\n".join([
                f"• #{order.order_number} - {order.bot_type} - Status: **{order.status.name}**"
                for order in active_orders
            ])
            embed.add_field(
                name=f"Active Orders ({len(active_orders)})",
                value=active_order_list,
                inline=False
            )
        
        # Add completed orders
        completed_orders = [order for order in orders if order.status.name == "COMPLETE"]
        if completed_orders:
            completed_order_list = "\n".join([
                f"• #{order.order_number} - {order.bot_type}"
                for order in completed_orders[:5]  # Show at most 5 to avoid too long embed
            ])
            
            if len(completed_orders) > 5:
                completed_order_list += f"\n• ... and {len(completed_orders) - 5} more"
                
            embed.add_field(
                name=f"Completed Orders ({len(completed_orders)})",
                value=completed_order_list,
                inline=False
            )
        
        # Add cancelled/rejected orders
        cancelled_orders = [order for order in orders if order.status.name in ["CANCELLED", "REJECTED"]]
        if cancelled_orders:
            cancelled_order_list = "\n".join([
                f"• #{order.order_number} - {order.bot_type} - **{order.status.name}**"
                for order in cancelled_orders[:3]  # Show at most 3
            ])
            
            if len(cancelled_orders) > 3:
                cancelled_order_list += f"\n• ... and {len(cancelled_orders) - 3} more"
                
            embed.add_field(
                name=f"Cancelled/Rejected Orders ({len(cancelled_orders)})",
                value=cancelled_order_list,
                inline=False
            )
        
        # Add note about order details
        embed.add_field(
            name="Need More Details?",
            value="Use `/order-status [order-number]` to see detailed information about a specific order.",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="payment-history", description="View your submitted Robux payments and order links")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def payment_history(self, interaction: discord.Interaction):
        """View your submitted Robux payments and order links."""
        # Check if user is registered
        if not await check_if_registered(interaction):
            return
        
        # Get user's payment history
        db = get_db()
        user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
        
        if not user or not user.payments:
            embed = create_basic_embed(
                "💸 Payment History", 
                "You haven't made any payments yet.",
                discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Create embed to display payment history
        embed = create_basic_embed(
            "💸 Payment History", 
            f"You have made {len(user.payments)} payments.",
            discord.Color.blue()
        )
        
        # Group payments by verification status
        verified_payments = [payment for payment in user.payments if payment.is_verified]
        pending_payments = [payment for payment in user.payments if not payment.is_verified]
        
        # Add pending payments
        if pending_payments:
            pending_list = "\n".join([
                f"• {payment.amount} Robux - Order #{payment.order.order_number} - Submitted <t:{int(payment.submitted_at.timestamp())}:R>"
                for payment in pending_payments
            ])
            
            embed.add_field(
                name=f"Pending Verification ({len(pending_payments)})",
                value=pending_list,
                inline=False
            )
        
        # Add verified payments
        if verified_payments:
            verified_list = "\n".join([
                f"• {payment.amount} Robux - Order #{payment.order.order_number} - Verified <t:{int(payment.verified_at.timestamp()) if payment.verified_at else 0}:R>"
                for payment in verified_payments[:5]  # Show at most 5
            ])
            
            if len(verified_payments) > 5:
                verified_list += f"\n• ... and {len(verified_payments) - 5} more"
                
            embed.add_field(
                name=f"Verified Payments ({len(verified_payments)})",
                value=verified_list,
                inline=False
            )
        
        # Add total spent
        total_robux = sum(payment.amount for payment in verified_payments)
        embed.add_field(
            name="Total Robux Spent",
            value=f"{total_robux} Robux on verified payments",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Profile(bot))
