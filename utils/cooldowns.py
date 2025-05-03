from discord import app_commands
import time
from discord.app_commands.errors import CommandOnCooldown
import asyncio
from datetime import datetime, timedelta
from functools import wraps

# Store cooldowns in memory
_cooldowns = {}

def cooldown(rate, per):
    """
    Custom cooldown decorator for app_commands since discord.py version might not have it
    
    Args:
        rate: Number of times command can be used before triggering cooldown
        per: Cooldown period in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction, *args, **kwargs):
            # Create a unique key for this command and user
            command_name = interaction.command.name
            user_id = interaction.user.id
            key = f"{command_name}:{user_id}"
            
            # Check if on cooldown
            current_time = time.time()
            if key in _cooldowns:
                last_used, uses = _cooldowns[key]
                # If cooldown period has passed, reset
                if current_time - last_used >= per:
                    _cooldowns[key] = (current_time, 1)
                # Otherwise check usage count
                elif uses >= rate:
                    remaining = int(per - (current_time - last_used))
                    embed = {
                        "title": "Command on Cooldown",
                        "description": f"This command is on cooldown. Try again in {remaining} seconds.",
                        "color": 0xFF0000
                    }
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                else:
                    # Increment usage count
                    _cooldowns[key] = (last_used, uses + 1)
            else:
                # First use
                _cooldowns[key] = (current_time, 1)
            
            # Execute command
            return await func(self, interaction, *args, **kwargs)
        return wrapper
    return decorator