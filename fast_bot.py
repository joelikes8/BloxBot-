import os
import sys
import discord
import asyncio
import logging
import importlib
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

# These functions will be pre-registered during startup to make the bot immediately usable
async def preload_commands():
    """Pre-register essential commands before connecting to Discord"""
    from discord import app_commands
    
    # Ping command - essential and doesn't conflict with cogs
    @bot.tree.command(name="ping", description="Check the bot's response time (latency).")
    async def ping_command(interaction: discord.Interaction):
        await interaction.response.send_message(f"Pong! Latency: {round(bot.latency * 1000)}ms", ephemeral=True)
    
    # Quick status command - doesn't conflict with regular status
    @bot.tree.command(name="online", description="Quick check if the bot is online.")
    async def online_command(interaction: discord.Interaction):
        await interaction.response.send_message("Bot is online and responding to commands.", ephemeral=True)
    
    # Pre-sync these basic commands
    try:
        await bot.tree.sync()
        logger.info("Pre-synced essential commands")
    except Exception as e:
        logger.error(f"Failed to pre-sync commands: {e}")

@bot.event
async def on_ready():
    """Event triggered when the bot is ready."""
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    
    # Set custom status immediately
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="for /help | Roblox Bot Orders"
    ))
    
    # Pre-register essential commands AFTER login
    await preload_commands()
    
    logger.info('Bot is ready with basic commands!')
    
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
        
        # Sync commands again with full command set
        logger.info("Syncing application commands...")
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Error in delayed setup: {e}")

async def main():
    """Entry point for the bot with register commands after login"""
    try:
        # Register commands only after login (in on_ready)
        # This ensures application ID is set
        await bot.start(TOKEN)
    except KeyboardInterrupt:
        await bot.close()
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    # Run the bot with minimal overhead
    asyncio.run(main())