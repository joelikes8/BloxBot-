import os
import discord
import logging
import asyncio
from dotenv import load_dotenv
from discord.ext import commands
from database.db import init_db

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('bot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    logger.error("No Discord token found in environment variables!")
    exit(1)

# Bot configuration
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents, help_command=None)

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

@bot.event
async def on_ready():
    """Event triggered when the bot is ready."""
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    
    # Sync application commands with Discord
    try:
        logger.info("Syncing application commands...")
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync application commands: {e}")
    
    logger.info('Bot is ready!')
    
    # Set custom status
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="for /help | Roblox Bot Orders"
    ))

async def load_extensions():
    """Load all extensions/cogs."""
    for extension in cogs:
        try:
            await bot.load_extension(extension)
            logger.info(f'Loaded extension: {extension}')
        except Exception as e:
            logger.error(f'Failed to load extension {extension}: {e}')

@bot.event
async def on_command_error(ctx, error):
    """Global error handler."""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.respond("Missing required argument. Please check the command usage with `/help`.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.respond("You don't have permission to use this command.")
    else:
        logger.error(f"Command error: {error}")
        await ctx.respond(f"An error occurred: {error}")

@bot.command(name='sync')
@commands.is_owner()
async def sync(ctx):
    """Sync app commands to Discord (owner only)."""
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"Synced {len(synced)} command(s)")
        logger.info(f"Force synced {len(synced)} command(s)")
    except Exception as e:
        await ctx.send(f"Failed to sync: {e}")
        logger.error(f"Failed to force sync application commands: {e}")

async def main_bot():
    """Main function to run the bot."""
    # Initialize the database
    init_db()
    
    # Load all cogs
    await load_extensions()
    
    # Start the bot
    async with bot:
        await bot.start(TOKEN)

# Import Flask app for gunicorn
from app import app

if __name__ == '__main__':
    asyncio.run(main_bot())
