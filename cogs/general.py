import discord
from discord import app_commands
from discord.ext import commands
import platform
import time
import datetime
from utils.embeds import create_basic_embed, create_help_embed, create_info_embed
from utils.constants import BOT_VERSION, BOT_UPDATE_LOG, DEFAULT_COOLDOWN
from utils.cooldowns import cooldown

class General(commands.Cog):
    """General commands for bot information and utilities."""
    
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
    
    @app_commands.command(name="help", description="View a full list of available commands and categories")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def help(self, interaction: discord.Interaction):
        """View a full list of available commands and categories."""
        embed = create_help_embed(interaction)
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="info", description="Displays information about the server and this bot")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def info(self, interaction: discord.Interaction):
        """Display information about the server and this bot."""
        embed = create_info_embed()
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="ping", description="Shows the bot's response time (latency)")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def ping(self, interaction: discord.Interaction):
        """Show the bot's response time (latency)."""
        start_time = time.time()
        
        # Respond to let the user know we received the command
        await interaction.response.defer()
        
        # Calculate response time
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000)
        
        # Get websocket latency
        api_latency = round(self.bot.latency * 1000)
        
        embed = create_basic_embed("🏓 Pong!", color=discord.Color.green())
        embed.add_field(name="API Latency", value=f"{api_latency} ms", inline=True)
        embed.add_field(name="Response Time", value=f"{response_time} ms", inline=True)
        
        await interaction.followup.send(embed=embed)
        
    @app_commands.command(name="uptime", description="See how long the bot has been running")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def uptime(self, interaction: discord.Interaction):
        """Show how long the bot has been running."""
        current_time = time.time()
        difference = current_time - self.start_time
        uptime = str(datetime.timedelta(seconds=int(difference)))
        
        embed = create_basic_embed("⏱️ Bot Uptime", color=discord.Color.blue())
        embed.add_field(name="Running Since", value=f"{uptime}", inline=False)
        embed.add_field(name="Started At", value=f"<t:{int(self.start_time)}:F>", inline=False)
        
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="status", description="Shows the bot version and recent update log")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def status_command(self, interaction: discord.Interaction):
        """Show the bot version and recent update log."""
        embed = create_basic_embed("🤖 Bot Status", color=discord.Color.gold())
        
        # Add version info
        embed.add_field(name="Bot Version", value=f"v{BOT_VERSION}", inline=True)
        embed.add_field(name="Discord.py Version", value=f"v{discord.__version__}", inline=True)
        embed.add_field(name="Python Version", value=f"v{platform.python_version()}", inline=True)
        
        # Add recent updates
        update_log = "\n".join(BOT_UPDATE_LOG)
        embed.add_field(name="Recent Updates", value=update_log, inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
