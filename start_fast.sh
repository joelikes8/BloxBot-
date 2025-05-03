#!/bin/bash

# Set environment variables for faster startup
export PYTHONOPTIMIZE=1        # Turn on basic optimizations
export PYTHONUNBUFFERED=1      # Remove output buffering for faster logs
export PYTHONIOENCODING=utf-8  # Set consistent encoding
export PYTHONASYNCIODEBUG=0    # Disable asyncio debug mode
export DISCORD_SKIP_EXTENSIVE_GUILD_CACHE=1  # Skip extensive guild caching for faster login

# Launch the fast bot implementation
echo "Starting Discord bot with optimized settings..."
exec python fast_bot.py