import discord
from discord import app_commands
from discord.ext import commands
from utils.helpers import check_if_registered
from utils.embeds import create_basic_embed, create_faq_embed
from utils.constants import DEFAULT_COOLDOWN, EMOJI_SUCCESS, EMOJI_ERROR, SUPPORT_SERVER_INVITE, SUPPORT_CONTACT
from utils.cooldowns import cooldown

class Utility(commands.Cog):
    """Utility commands for reporting issues and getting help."""
    
    def __init__(self, bot):
        self.bot = bot
    
    class ReportModal(discord.ui.Modal, title="Report an Issue"):
        """Modal for reporting a bug or issue."""
        
        issue_type = discord.ui.Select(
            placeholder="Select Issue Type",
            options=[
                discord.SelectOption(label="Bot Bug", value="bot_bug", description="Issue with your custom Roblox bot"),
                discord.SelectOption(label="Discord Bot Bug", value="discord_bug", description="Issue with this Discord bot"),
                discord.SelectOption(label="Payment Issue", value="payment", description="Problem with payment or verification"),
                discord.SelectOption(label="Other", value="other", description="Other type of issue")
            ]
        )
        
        order_number = discord.ui.TextInput(
            label="Order Number (if applicable)",
            placeholder="Leave empty if not related to a specific order",
            required=False,
            max_length=10
        )
        
        description = discord.ui.TextInput(
            label="Issue Description",
            style=discord.TextStyle.paragraph,
            placeholder="Describe the issue in detail. Include any error messages or steps to reproduce.",
            required=True,
            max_length=1000
        )
        
        async def on_submit(self, interaction: discord.Interaction):
            # Create an embed with the report details
            issue_type_name = next((option.label for option in self.issue_type.options if option.value == self.issue_type.values[0]), "Unknown")
            
            embed = create_basic_embed(
                f"🐛 New Issue Report: {issue_type_name}", 
                self.description.value,
                discord.Color.red()
            )
            
            embed.add_field(
                name="Reported By",
                value=f"{interaction.user.name} ({interaction.user.mention})",
                inline=True
            )
            
            embed.add_field(
                name="Issue Type",
                value=issue_type_name,
                inline=True
            )
            
            if self.order_number.value:
                embed.add_field(
                    name="Order Number",
                    value=self.order_number.value,
                    inline=True
                )
            
            # Try to send to reports channel
            try:
                # This would normally send to a dedicated reports channel
                # Since we don't have access to that, we'll send to the current channel
                await interaction.channel.send(embed=embed)
                
                # Confirm to the user
                await interaction.response.send_message(
                    f"{EMOJI_SUCCESS} Your issue has been reported! Our team will look into it as soon as possible.",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"{EMOJI_ERROR} Failed to submit your report: {str(e)}",
                    ephemeral=True
                )
    
    @app_commands.command(name="report", description="Report a bug or problem with your bot")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def report(self, interaction: discord.Interaction):
        """Report a bug or problem with your bot."""
        # Check if user is registered
        if not await check_if_registered(interaction):
            return
        
        # Show the report modal
        await interaction.response.send_modal(self.ReportModal())
    
    @app_commands.command(name="support", description="Shows how to contact staff or get help")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def support(self, interaction: discord.Interaction):
        """Show how to contact staff or get help."""
        embed = create_basic_embed(
            "🆘 Support Information", 
            "Need help with your order or have questions? Here's how to get support:",
            discord.Color.blue()
        )
        
        embed.add_field(
            name="For Order Issues",
            value=(
                "• Use `/report` to submit a detailed bug report\n"
                "• Use `/order-status [order-number]` to check your order status\n"
                "• Contact a staff member directly for urgent issues"
            ),
            inline=False
        )
        
        embed.add_field(
            name="For Payment Issues",
            value=(
                "• Use `/submit-payment` to submit payment proof\n"
                "• If your payment was rejected, check the reason and submit again\n"
                "• For refund requests, contact an admin"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Contact Methods",
            value=(
                f"• Join our support server: {SUPPORT_SERVER_INVITE}\n"
                f"• {SUPPORT_CONTACT}"
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="faq", description="View answers to common questions and concerns")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def faq(self, interaction: discord.Interaction):
        """View answers to common questions and concerns."""
        embed = create_faq_embed()
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
