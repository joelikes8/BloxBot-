# Bot settings
BOT_VERSION = "1.0.0"
DEFAULT_COOLDOWN = 5  # Cooldown in seconds for most commands
ADMIN_COOLDOWN = 3    # Cooldown for admin commands
EMOJI_SUCCESS = "✅"   # Emoji for success messages
EMOJI_ERROR = "❌"     # Emoji for error messages
EMOJI_WARNING = "⚠️"   # Emoji for warning messages
EMOJI_INFO = "ℹ️"      # Emoji for info messages

# Support
SUPPORT_SERVER_INVITE = "https://discord.gg/robloxbotorders"
SUPPORT_CONTACT = "support@robloxbotorders.com"

# Status descriptions for different order statuses
STATUS_DESCRIPTIONS = {
    "PENDING": "Awaiting initial review",
    "PAYMENT_WAITING": "Waiting for payment confirmation",
    "PAYMENT_RECEIVED": "Payment received, preparing to start work",
    "IN_PROGRESS": "Currently being developed",
    "REVIEW": "In final testing phase",
    "COMPLETE": "Ready for delivery",
    "CANCELLED": "Order cancelled",
    "REJECTED": "Order rejected"
}

# Bot update log
BOT_UPDATE_LOG = [
    "• 1.0.0: Initial release with all core functionality",
    "• Added user profile management",
    "• Added order management system",
    "• Added payment verification system",
    "• Added staff commands for order management"
]

# Bot types offered
BOT_TYPES = [
    "Economy Bot",
    "Moderation Bot",
    "Game Bot",
    "Leaderboard Bot",
    "Utility Bot",
    "Custom Bot"
]

# Price ranges based on bot type (in Robux)
BOT_PRICES = {
    "Economy Bot": (8000, 15000),
    "Moderation Bot": (5000, 10000),
    "Game Bot": (12000, 25000),
    "Leaderboard Bot": (4000, 8000),
    "Utility Bot": (3000, 7000),
    "Custom Bot": (10000, 30000)
}

# Order status messages
STATUS_MESSAGES = {
    "pending": "Your order has been received and is awaiting review.",
    "payment_waiting": "Your order has been accepted. Please submit payment.",
    "payment_received": "Payment received and verified. Work will begin soon.",
    "in_progress": "Your bot is currently being developed.",
    "review": "Your bot is complete and awaiting final testing.",
    "complete": "Your bot is finished and ready for delivery!",
    "cancelled": "This order has been cancelled.",
    "rejected": "Your order could not be fulfilled."
}

# Admin and support roles
ADMIN_ROLE_ID = 123456789012345678
STAFF_ROLE_ID = 123456789012345680
SUPPORT_ROLE_ID = 123456789012345682

# Channel IDs
ORDER_CHANNEL_ID = 123456789012345690
PAYMENT_CHANNEL_ID = 123456789012345692
ANNOUNCEMENT_CHANNEL_ID = 123456789012345694