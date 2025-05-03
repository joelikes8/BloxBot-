import discord
import datetime
from database.db import get_db
from database.models import User, Order, OrderState, Payment
from utils.constants import EMOJI_ERROR, EMOJI_SUCCESS, EMOJI_WARNING
from utils.embeds import create_basic_embed

async def check_if_registered(interaction):
    """Check if a user is registered, and send an error message if not."""
    db = get_db()
    user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
    
    if not user:
        embed = create_basic_embed(
            f"{EMOJI_ERROR} Not Registered", 
            "You haven't registered yet! Use `/register` to create your profile.",
            discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False
    
    return True

def get_or_create_user(discord_id, discord_name):
    """Get an existing user or create a new one if they don't exist."""
    db = get_db()
    user = db.query(User).filter(User.discord_id == str(discord_id)).first()
    
    if not user:
        user = User(
            discord_id=str(discord_id),
            discord_name=discord_name
        )
        db.add(user)
        db.commit()
    
    return user

def get_user_orders(discord_id):
    """Get all orders for a specific user."""
    db = get_db()
    user = db.query(User).filter(User.discord_id == str(discord_id)).first()
    
    if not user:
        return []
    
    # Return orders sorted by creation date (newest first)
    return db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()

def get_order_by_number(order_number):
    """Get an order by its unique order number."""
    db = get_db()
    return db.query(Order).filter(Order.order_number == order_number).first()

def generate_order_number():
    """Generate a unique order number."""
    import random
    import string
    
    # Generate a random number in format ABC-1234
    prefix = ''.join(random.choices(string.ascii_uppercase, k=3))
    suffix = ''.join(random.choices(string.digits, k=4))
    order_number = f"{prefix}-{suffix}"
    
    # Check if the order number already exists
    db = get_db()
    existing_order = db.query(Order).filter(Order.order_number == order_number).first()
    
    # If it exists, recursively generate another one
    if existing_order:
        return generate_order_number()
    
    return order_number

def calculate_price(bot_type, features):
    """Calculate the price based on bot type and features."""
    from utils.constants import BOT_PRICES
    
    # Get base price range for the bot type
    min_price, max_price = BOT_PRICES.get(bot_type, (5000, 15000))
    
    # Count the number of features
    feature_count = len(features.split('\n'))
    
    # Calculate the price based on the number of features
    if feature_count <= 3:
        # Few features, use the minimum price
        price = min_price
    elif feature_count <= 6:
        # Medium number of features, use the middle of the range
        price = (min_price + max_price) / 2
    else:
        # Many features, use the maximum price
        price = max_price
    
    # Round to the nearest 100
    return round(price / 100) * 100

def has_admin_role(interaction):
    """Check if a user has an admin role."""
    from utils.constants import ADMIN_ROLE_ID, STAFF_ROLE_ID
    
    # Check if the user has either admin or staff role
    for role in interaction.user.roles:
        if role.id in [ADMIN_ROLE_ID, STAFF_ROLE_ID]:
            return True
    
    return False

def has_staff_role(interaction):
    """Check if a user has a staff role."""
    from utils.constants import STAFF_ROLE_ID, ADMIN_ROLE_ID, SUPPORT_ROLE_ID
    
    # Check if the user has any staff role
    for role in interaction.user.roles:
        if role.id in [ADMIN_ROLE_ID, STAFF_ROLE_ID, SUPPORT_ROLE_ID]:
            return True
    
    return False

async def check_if_staff(interaction):
    """Check if a user is a staff member, and send an error message if not."""
    if not has_staff_role(interaction):
        embed = create_basic_embed(
            f"{EMOJI_ERROR} Not Authorized", 
            "You don't have permission to use this command.",
            discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False
    
    return True

async def create_order(user_id, bot_type, features, notes=None):
    """Create a new order in the database."""
    order_number = generate_order_number()
    price = calculate_price(bot_type, features)
    
    db = get_db()
    
    new_order = Order(
        user_id=user_id,
        order_number=order_number,
        bot_type=bot_type,
        features=features,
        notes=notes,
        price=price,
        status=OrderState.PENDING
    )
    
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    return new_order

def update_order_status(order_id, new_status, changed_by, comment=None):
    """Update the status of an order and add a status update record."""
    from database.models import OrderStatus
    
    db = get_db()
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        return None
    
    # Update the order status
    old_status = order.status
    order.status = new_status
    
    # If completing the order, set the completion date
    if new_status == OrderState.COMPLETE:
        order.completed_at = datetime.datetime.utcnow()
    
    # Create a status update record
    status_update = OrderStatus(
        order_id=order_id,
        status=new_status,
        comment=comment,
        changed_by=changed_by
    )
    
    db.add(status_update)
    db.commit()
    
    return order

async def create_payment(discord_id, order_id, amount, proof_url):
    """Create a new payment record in the database."""
    from database.models import User
    
    db = get_db()
    
    # Get the user record by discord_id
    user = db.query(User).filter(User.discord_id == str(discord_id)).first()
    
    if not user:
        return None
    
    new_payment = Payment(
        user_id=user.id,  # Use the internal user ID from the database
        order_id=order_id,
        amount=amount,
        proof_url=proof_url,
        is_verified=False,
        submitted_at=datetime.datetime.utcnow()
    )
    
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    
    return new_payment

def toggle_subscription(discord_id, order_updates=None, announcements=None):
    """Toggle a user's subscription preferences."""
    from database.models import User, Subscription
    
    db = get_db()
    
    # Get the user record by discord_id
    user = db.query(User).filter(User.discord_id == str(discord_id)).first()
    
    if not user:
        return None
    
    # Now find the subscription using the user's internal ID
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    
    # Create a new subscription if it doesn't exist
    if not subscription:
        subscription = Subscription(
            user_id=user.id,  # Use the internal user ID from the database
            order_updates=True if order_updates is None else order_updates,
            announcements=True if announcements is None else announcements
        )
        db.add(subscription)
    else:
        # Update existing subscription
        if order_updates is not None:
            subscription.order_updates = order_updates
        if announcements is not None:
            subscription.announcements = announcements
    
    db.commit()
    return subscription

async def check_if_admin(interaction):
    """Check if a user is an admin, and send an error message if not."""
    if not has_admin_role(interaction):
        embed = create_basic_embed(
            f"{EMOJI_ERROR} Admin Required", 
            "This command requires administrator privileges.",
            discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False
    
    return True

def get_daily_tip():
    """Get a random daily tip or bot idea."""
    import random
    
    tips = [
        "Consider adding a help command that shows all available commands.",
        "Economy bots are popular - try adding fun mini-games for earning currency.",
        "Make your bot stand out with custom emojis and a unique personality.",
        "Use webhooks for sending customized messages to announcement channels.",
        "Add role-based permissions to restrict certain commands.",
        "Implement a ticket system for user support and inquiries.",
        "Create a leveling system to reward active users.",
        "Consider adding moderation features like warn, mute, and ban commands.",
        "Implement a custom prefix to avoid conflicts with other bots.",
        "Add reaction roles for easier role assignment.",
        "Consider adding a suggestion system for server improvements.",
        "Implement a giveaway system for community engagement.",
        "Add a reminder system for scheduled events or tasks.",
        "Create a poll system for community voting.",
        "Implement a welcome message for new server members."
    ]
    
    return random.choice(tips)

async def create_notification(discord_id, message, order_id=None):
    """Create a notification for a user."""
    from database.models import User, Notification
    
    db = get_db()
    
    # Get the user record by discord_id
    user = db.query(User).filter(User.discord_id == str(discord_id)).first()
    
    if not user:
        return None
    
    notification = Notification(
        user_id=user.id,  # Use the internal user ID from the database
        order_id=order_id,
        message=message,
        is_read=False,
        created_at=datetime.datetime.utcnow()
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    return notification

def verify_payment(payment_id, is_verified=True, verified_by="System"):
    """Verify a payment record."""
    db = get_db()
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        return None
    
    # Update payment verification status
    payment.is_verified = is_verified
    payment.verified_at = datetime.datetime.utcnow() if is_verified else None
    
    # Update the order status if payment is verified
    if is_verified:
        order = db.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            old_status = order.status
            order.status = OrderState.PAYMENT_RECEIVED
            
            # Add status update record
            from database.models import OrderStatus
            status_update = OrderStatus(
                order_id=order.id,
                status=OrderState.PAYMENT_RECEIVED,
                comment="Payment verified",
                changed_by=verified_by
            )
            db.add(status_update)
    
    db.commit()
    return payment