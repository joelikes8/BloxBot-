import discord
import datetime
from utils.constants import BOT_TYPES, BOT_PRICES, BOT_VERSION, STATUS_MESSAGES

def format_timestamp(timestamp):
    """Format a datetime object into a readable string."""
    return f"<t:{int(timestamp.timestamp())}:F>"

def create_basic_embed(title, description=None, color=discord.Color.blue()):
    """Create a basic Discord embed."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text=f"Roblox Bot Orders v{BOT_VERSION}")
    return embed

def create_help_embed(interaction):
    """Create a help embed with all command categories."""
    embed = create_basic_embed("Bot Commands", 
                              "Here are all available commands organized by category.",
                              discord.Color.blurple())
    
    # Get the bot from the interaction
    bot = interaction.client
    
    # Group commands by cog (category)
    for cog_name, cog in bot.cogs.items():
        # Skip empty cogs
        if not cog.get_app_commands():
            continue
        
        # Get the cog description
        description = cog.__doc__ or "No description available."
        
        # Create field for each category
        command_list = []
        for command in cog.get_app_commands():
            command_list.append(f"• `/{command.name}` - {command.description}")
        
        if command_list:
            embed.add_field(
                name=f"📌 {cog_name}",
                value=f"{description}\n{''.join(command_list)}\n",
                inline=False
            )
    
    return embed

def create_info_embed():
    """Create an info embed with server and bot information."""
    embed = create_basic_embed("Bot Information", 
                              "Information about the Roblox Bot Orders system.",
                              discord.Color.gold())
    
    # Bot information
    embed.add_field(name="📝 Description", 
                   value="This bot helps manage custom Roblox bot orders, payments, and delivery.", 
                   inline=False)
    
    embed.add_field(name="🤖 Bot Types", 
                   value=", ".join(BOT_TYPES), 
                   inline=False)
    
    embed.add_field(name="💰 Price Range", 
                   value="3,000 - 30,000 Robux depending on complexity", 
                   inline=True)
    
    embed.add_field(name="⏱️ Typical Delivery", 
                   value="3-14 days", 
                   inline=True)
    
    # Support information
    embed.add_field(name="🔧 Support", 
                   value="Use `/support` for help or `/report` for issues", 
                   inline=False)
    
    return embed

def create_profile_embed(user, discord_user):
    """Create a profile embed for a user."""
    embed = create_basic_embed(f"{discord_user.name}'s Profile", 
                              f"Account information and order statistics",
                              discord.Color.purple())
    
    # User information
    embed.set_thumbnail(url=discord_user.display_avatar.url)
    embed.add_field(name="Discord Name", value=discord_user.name, inline=True)
    embed.add_field(name="Registered Since", 
                   value=format_timestamp(user.registration_date), 
                   inline=True)
    
    # Roblox information if available
    if user.roblox_username:
        embed.add_field(name="Roblox Username", 
                       value=user.roblox_username, 
                       inline=True)
    
    # Order statistics
    total_orders = len(user.orders)
    completed_orders = sum(1 for order in user.orders if order.status.name == "COMPLETE")
    pending_orders = sum(1 for order in user.orders if order.status.name in ["PENDING", "PAYMENT_WAITING", "IN_PROGRESS"])
    
    embed.add_field(name="📊 Order Statistics", 
                   value=f"Total Orders: {total_orders}\nCompleted: {completed_orders}\nPending/Active: {pending_orders}", 
                   inline=False)
    
    return embed

def create_order_embed(order):
    """Create an embed for an order."""
    # Choose color based on status
    status_colors = {
        "PENDING": discord.Color.light_grey(),
        "PAYMENT_WAITING": discord.Color.gold(),
        "PAYMENT_RECEIVED": discord.Color.green(),
        "IN_PROGRESS": discord.Color.blue(),
        "REVIEW": discord.Color.purple(),
        "COMPLETE": discord.Color.green(),
        "CANCELLED": discord.Color.red(),
        "REJECTED": discord.Color.red()
    }
    
    color = status_colors.get(order.status.name, discord.Color.default())
    
    embed = create_basic_embed(f"Order #{order.order_number}", 
                              STATUS_MESSAGES.get(order.status.name.lower(), "No status information available."),
                              color)
    
    # Order details
    embed.add_field(name="Bot Type", value=order.bot_type, inline=True)
    embed.add_field(name="Price", value=f"{int(order.price):,} Robux", inline=True)
    embed.add_field(name="Created", 
                   value=format_timestamp(order.created_at), 
                   inline=True)
    
    # Format features as a list
    features_list = order.features.split("\n")
    features_formatted = "\n".join([f"• {feature}" for feature in features_list])
    
    embed.add_field(name="Requested Features", 
                   value=features_formatted, 
                   inline=False)
    
    # Add notes if available
    if order.notes:
        embed.add_field(name="Additional Notes", 
                       value=order.notes, 
                       inline=False)
    
    # Status information
    status_text = f"📋 **Current Status:** {order.status.name.replace('_', ' ').title()}"
    
    # Add completion date if completed
    if order.status.name == "COMPLETE" and order.completed_at:
        status_text += f"\n✅ **Completed:** {format_timestamp(order.completed_at)}"
    
    embed.add_field(name="Status Information", 
                   value=status_text, 
                   inline=False)
    
    return embed

def create_pricing_embed():
    """Create an embed showing pricing information."""
    embed = create_basic_embed("Bot Pricing Information", 
                              "Detailed pricing for different bot types and features.",
                              discord.Color.gold())
    
    # Bot type pricing
    pricing_text = ""
    for bot_type, price_range in BOT_PRICES.items():
        min_price, max_price = price_range
        pricing_text += f"**{bot_type}:** {min_price:,} - {max_price:,} Robux\n"
    
    embed.add_field(name="Bot Type Pricing", 
                   value=pricing_text, 
                   inline=False)
    
    # Feature pricing
    embed.add_field(name="Additional Features", 
                   value="Each additional feature beyond the basic package may increase the price by 1,000-5,000 Robux depending on complexity.", 
                   inline=False)
    
    # Payment information
    embed.add_field(name="Payment Methods", 
                   value="Payments are accepted in Robux only through group funds or game passes.", 
                   inline=False)
    
    # Discounts information
    embed.add_field(name="Discounts", 
                   value="• 10% off for returning customers\n• 15% off for orders over 20,000 Robux\n• Special rates for bulk orders (multiple bots)", 
                   inline=False)
    
    return embed

def create_faq_embed():
    """Create an embed with frequently asked questions."""
    embed = create_basic_embed("Frequently Asked Questions", 
                              "Answers to common questions about our bot services.",
                              discord.Color.blurple())
    
    # Add FAQ items
    embed.add_field(name="How long does it take to complete an order?", 
                   value="Most orders are completed within 3-14 days, depending on complexity and current workload.", 
                   inline=False)
    
    embed.add_field(name="How do I pay for my order?", 
                   value="Payment is accepted in Robux through group funds or game pass purchases. After your order is confirmed, you'll receive payment instructions.", 
                   inline=False)
    
    embed.add_field(name="What happens after I submit an order?", 
                   value="1. Your order is reviewed by staff\n2. You receive a price quote\n3. After payment, development begins\n4. You'll receive updates throughout the process\n5. Final delivery and instructions are provided", 
                   inline=False)
    
    embed.add_field(name="Can I request changes to my bot?", 
                   value="Minor changes during development are included. Major changes after the requirements are confirmed may incur additional costs.", 
                   inline=False)
    
    embed.add_field(name="Do you offer refunds?", 
                   value="Partial refunds may be available if work hasn't progressed significantly. Once development is substantially complete, refunds are not provided.", 
                   inline=False)
    
    embed.add_field(name="How do I get support after delivery?", 
                   value="Basic support and bug fixes are included for 30 days after delivery. Extended support packages are available for purchase.", 
                   inline=False)
    
    return embed