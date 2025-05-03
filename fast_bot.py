import os
import discord
import asyncio
import logging
from dotenv import load_dotenv
from discord.ext import commands

# Configure minimal logging for faster startup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('bot')

# Load environment variables (faster than full database initialization at first)
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    logger.error("No Discord token found in environment variables!")
    exit(1)

# Optimize intents by only enabling what's needed
intents = discord.Intents.default()
intents.members = True  # Need members intent for user commands
intents.message_content = True  # Need message content for commands

# Create bot with minimal configuration
bot = commands.Bot(command_prefix='/', intents=intents, help_command=None)

@bot.event
async def on_ready():
    """Event triggered when the bot is ready."""
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info('Bot is ready!')
    
    # Set custom status after login
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="for /help | Roblox Bot Orders"
    ))
    
    # Initialize database and load extensions asynchronously
    asyncio.create_task(delayed_setup())

async def delayed_setup():
    """Load all resources after bot is already connected."""
    try:
        # Import here to avoid slowing initial connection
        from database.db import init_db
        
        # Initialize the database
        init_db()
        
        # List of cogs to load
        cogs = [
            'cogs.general',
            'cogs.profile',
            'cogs.orders',
            'cogs.notifications',
            'cogs.admin',
            'cogs.extras',
            'cogs.utility'
        ]
        
        # Load all extensions/cogs
        for extension in cogs:
            try:
                await bot.load_extension(extension)
                logger.info(f'Loaded extension: {extension}')
            except Exception as e:
                logger.error(f'Failed to load extension {extension}: {e}')
        
        # Sync commands after everything is loaded
        logger.info("Syncing application commands...")
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Error in delayed setup: {e}")

if __name__ == "__main__":
    # Run the bot with minimal overhead
    bot.run(TOKEN, log_handler=None)  # Disable discord.py's built-in logging