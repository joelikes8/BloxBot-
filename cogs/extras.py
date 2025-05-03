import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import datetime
from utils.helpers import check_if_staff, get_daily_tip
from utils.embeds import create_basic_embed
from utils.cooldowns import cooldown
from database.db import get_db
from database.models import User, Order
from utils.constants import DEFAULT_COOLDOWN, EMOJI_SUCCESS, EMOJI_ERROR

class Extras(commands.Cog):
    """Extra commands for community engagement and fun features."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="giveaway", description="Start a giveaway (Robux, free bots, perks)")
    @cooldown(1, DEFAULT_COOLDOWN)
    @app_commands.describe(
        prize="The prize to give away",
        duration="Duration in minutes",
        winners="Number of winners"
    )
    async def giveaway(
        self, 
        interaction: discord.Interaction, 
        prize: str, 
        duration: int = 60, 
        winners: int = 1
    ):
        """Start a giveaway (Robux, free bots, perks)."""
        # Check if user is staff
        if not await check_if_staff(interaction):
            return
        
        # Validate inputs
        if duration < 1 or duration > 10080:  # 10080 minutes = 1 week
            await interaction.response.send_message(
                f"{EMOJI_ERROR} Duration must be between 1 minute and 1 week (10080 minutes).",
                ephemeral=True
            )
            return
        
        if winners < 1 or winners > 10:
            await interaction.response.send_message(
                f"{EMOJI_ERROR} Number of winners must be between 1 and 10.",
                ephemeral=True
            )
            return
        
        # Calculate end time
        end_time = datetime.datetime.now() + datetime.timedelta(minutes=duration)
        
        # Create giveaway embed
        embed = create_basic_embed(
            "🎉 Giveaway!", 
            f"React with 🎉 to enter this giveaway!",
            discord.Color.gold()
        )
        
        embed.add_field(
            name="Prize",
            value=prize,
            inline=False
        )
        
        embed.add_field(
            name="Winners",
            value=str(winners),
            inline=True
        )
        
        embed.add_field(
            name="Hosted By",
            value=interaction.user.mention,
            inline=True
        )
        
        embed.add_field(
            name="Ends At",
            value=f"<t:{int(end_time.timestamp())}:F> (<t:{int(end_time.timestamp())}:R>)",
            inline=False
        )
        
        # Send the giveaway message
        await interaction.response.send_message("🎉 Creating giveaway...", ephemeral=True)
        giveaway_message = await interaction.channel.send(embed=embed)
        
        # Add the reaction
        await giveaway_message.add_reaction("🎉")
        
        # Wait for the giveaway to end
        await asyncio.sleep(duration * 60)
        
        # Fetch the message again to get updated reactions
        giveaway_message = await interaction.channel.fetch_message(giveaway_message.id)
        
        # Get the users who reacted
        try:
            reaction = next(reaction for reaction in giveaway_message.reactions if str(reaction.emoji) == "🎉")
            users = [user async for user in reaction.users() if not user.bot]
            
            if not users:
                # No participants
                end_embed = create_basic_embed(
                    "🎉 Giveaway Ended", 
                    f"No one participated in the giveaway for **{prize}**.",
                    discord.Color.red()
                )
                
                await giveaway_message.edit(embed=end_embed)
                await interaction.channel.send("No one participated in the giveaway! 😢")
                return
            
            # Select winners
            if len(users) <= winners:
                selected_winners = users
            else:
                selected_winners = random.sample(users, winners)
            
            # Create winners string
            winners_text = ", ".join([winner.mention for winner in selected_winners])
            
            # Update the giveaway embed
            end_embed = create_basic_embed(
                "🎉 Giveaway Ended", 
                f"Congratulations to the winners of **{prize}**!",
                discord.Color.gold()
            )
            
            end_embed.add_field(
                name=f"Winner{'s' if winners > 1 else ''}",
                value=winners_text,
                inline=False
            )
            
            end_embed.add_field(
                name="Hosted By",
                value=interaction.user.mention,
                inline=True
            )
            
            end_embed.add_field(
                name="Total Entries",
                value=str(len(users)),
                inline=True
            )
            
            await giveaway_message.edit(embed=end_embed)
            
            # Send a notification message
            await interaction.channel.send(
                f"🎉 Congratulations {winners_text}! You won the giveaway for **{prize}**!"
            )
            
        except Exception as e:
            # Handle errors
            error_embed = create_basic_embed(
                "❌ Giveaway Error", 
                f"An error occurred while ending the giveaway: {str(e)}",
                discord.Color.red()
            )
            
            await giveaway_message.edit(embed=error_embed)
    
    @app_commands.command(name="daily-tip", description="Posts a random bot idea or helpful tip")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def daily_tip(self, interaction: discord.Interaction):
        """Post a random bot idea or helpful tip."""
        tip = get_daily_tip()
        
        embed = create_basic_embed(
            "💡 Daily Bot Tip", 
            tip,
            discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="suggest", description="Submit feedback or ideas to improve the server")
    @app_commands.describe(suggestion="Your suggestion or feedback")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def suggest(self, interaction: discord.Interaction, suggestion: str):
        """Submit feedback or ideas to improve the server."""
        embed = create_basic_embed(
            "💡 New Suggestion", 
            suggestion,
            discord.Color.purple()
        )
        
        embed.add_field(
            name="Suggested By",
            value=f"{interaction.user.name} ({interaction.user.mention})",
            inline=True
        )
        
        embed.add_field(
            name="Suggestion Time",
            value=f"<t:{int(datetime.datetime.now().timestamp())}:F>",
            inline=True
        )
        
        # Send the suggestion to the channel
        suggestion_message = await interaction.channel.send(embed=embed)
        
        # Add voting reactions
        await suggestion_message.add_reaction("👍")
        await suggestion_message.add_reaction("👎")
        
        # Send confirmation to the user
        await interaction.response.send_message(
            f"{EMOJI_SUCCESS} Your suggestion has been submitted! Thank you for your feedback.",
            ephemeral=True
        )
    
    @app_commands.command(name="vote", description="Link to vote for the server or bot on top.gg")
    @cooldown(1, DEFAULT_COOLDOWN)
    async def vote(self, interaction: discord.Interaction):
        """Link to vote for the server or bot on top.gg."""
        embed = create_basic_embed(
            "🗳️ Vote for Us!", 
            "Support us by voting on these platforms!",
            discord.Color.blue()
        )
        
        embed.add_field(
            name="Top.gg",
            value="[Vote for our Bot on Top.gg](https://top.gg/bot/yourbot)",
            inline=True
        )
        
        embed.add_field(
            name="Discord Server List",
            value="[Vote for our Server](https://discord.st/server/yourserer)",
            inline=True
        )
        
        embed.add_field(
            name="Benefits of Voting",
            value="• Show your support for our community\n• Help us grow and reach more users\n• Exclusive voter role in our server",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="leaderboard", description="See the top buyers or most active users")
    @app_commands.describe(category="The leaderboard category to view")
    @app_commands.choices(category=[
        app_commands.Choice(name="Top Buyers", value="buyers"),
        app_commands.Choice(name="Most Orders", value="orders"),
        app_commands.Choice(name="Newest Users", value="newest")
    ])
    @cooldown(1, DEFAULT_COOLDOWN)
    async def leaderboard(
        self, 
        interaction: discord.Interaction, 
        category: app_commands.Choice[str] = None
    ):
        """See the top buyers or most active users."""
        if not category:
            category = app_commands.Choice(name="Top Buyers", value="buyers")
        
        db = get_db()
        
        if category.value == "buyers":
            # Get users with the most total payment amount
            users = db.query(User).join(User.payments).filter(User.payments != None).all()
            
            # Calculate total spent for each user
            user_totals = []
            for user in users:
                total_spent = sum(payment.amount for payment in user.payments if payment.is_verified)
                if total_spent > 0:
                    user_totals.append((user, total_spent))
            
            # Sort by total spent
            user_totals.sort(key=lambda x: x[1], reverse=True)
            
            # Create embed
            embed = create_basic_embed(
                "💰 Top Buyers Leaderboard", 
                "Users who have spent the most Robux on orders",
                discord.Color.gold()
            )
            
            # Add leaderboard entries
            if not user_totals:
                embed.add_field(
                    name="No Data",
                    value="No verified payments found yet!",
                    inline=False
                )
            else:
                leaderboard_text = ""
                for i, (user, total) in enumerate(user_totals[:10]):
                    medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                    
                    # Try to get the Discord user
                    discord_user = None
                    try:
                        discord_user = await self.bot.fetch_user(int(user.discord_id))
                    except:
                        pass
                    
                    name = discord_user.name if discord_user else user.discord_name
                    leaderboard_text += f"{medal} **{name}** - {total} Robux\n"
                
                embed.description = leaderboard_text
        
        elif category.value == "orders":
            # Get users with the most orders
            users = db.query(User).join(User.orders).filter(User.orders != None).all()
            
            # Count orders for each user
            user_orders = [(user, len(user.orders)) for user in users if user.orders]
            
            # Sort by order count
            user_orders.sort(key=lambda x: x[1], reverse=True)
            
            # Create embed
            embed = create_basic_embed(
                "📦 Most Orders Leaderboard", 
                "Users who have placed the most bot orders",
                discord.Color.blue()
            )
            
            # Add leaderboard entries
            if not user_orders:
                embed.add_field(
                    name="No Data",
                    value="No orders found yet!",
                    inline=False
                )
            else:
                leaderboard_text = ""
                for i, (user, count) in enumerate(user_orders[:10]):
                    medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                    
                    # Try to get the Discord user
                    discord_user = None
                    try:
                        discord_user = await self.bot.fetch_user(int(user.discord_id))
                    except:
                        pass
                    
                    name = discord_user.name if discord_user else user.discord_name
                    leaderboard_text += f"{medal} **{name}** - {count} orders\n"
                
                embed.description = leaderboard_text
        
        else:  # newest
            # Get newest registered users
            users = db.query(User).order_by(User.registration_date.desc()).limit(10).all()
            
            # Create embed
            embed = create_basic_embed(
                "🆕 Newest Users", 
                "Recently registered users in our system",
                discord.Color.green()
            )
            
            # Add leaderboard entries
            if not users:
                embed.add_field(
                    name="No Data",
                    value="No users found yet!",
                    inline=False
                )
            else:
                leaderboard_text = ""
                for i, user in enumerate(users):
                    # Try to get the Discord user
                    discord_user = None
                    try:
                        discord_user = await self.bot.fetch_user(int(user.discord_id))
                    except:
                        pass
                    
                    name = discord_user.name if discord_user else user.discord_name
                    registration_time = f"<t:{int(user.registration_date.timestamp())}:R>"
                    leaderboard_text += f"{i+1}. **{name}** - Joined {registration_time}\n"
                
                embed.description = leaderboard_text
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Extras(bot))
