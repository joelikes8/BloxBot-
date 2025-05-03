# BloxBot - Discord Bot for Roblox Bot Orders

A comprehensive Discord bot designed to manage Roblox bot orders, user profiles, and administrative tasks.

## Features

- **Order Management**: Create, track, and manage bot orders
- **User Profiles**: Register and link Discord accounts with Roblox usernames
- **Payment System**: Submit and verify Robux payments
- **Notification System**: Get updates about order progress and announcements
- **Administrative Tools**: Manage users, orders, and payments
- **Web Dashboard**: Monitor bot status and server activity

## Commands

The bot includes various command categories:

- **General**: Help, info, ping, uptime, status
- **Profile**: User profile management, registration, Roblox account linking
- **Orders**: Place orders, check status, submit payments, view pricing
- **Notifications**: Subscribe/unsubscribe to updates
- **Admin**: Review payments, update order status, moderation commands
- **Extras**: Giveaways, daily tips, suggestions, leaderboards
- **Utility**: Report issues, access support, view FAQs

## Technical Details

- Built with Python and Discord.py
- PostgreSQL database for data persistence
- Flask web dashboard for monitoring
- Modular design using Discord.py cogs
- Custom cooldown systems and error handling

## Deployment on Render

### Using render.yaml (Recommended)

1. Fork or clone this repository to your GitHub account
2. Connect your GitHub account to Render
3. Create a new Web Service on Render, pointing to your repository
4. Render will automatically detect the `render.yaml` file and set up the services
5. Add your `DISCORD_TOKEN` as an environment variable in Render dashboard

### Manual Setup

If you prefer to set up the services manually:

#### Discord Bot (Worker Service)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `bash start_fast.sh` (for faster login) or `python main.py`
- **Environment Variables**:
  - `PYTHON_VERSION`: 3.11.0
  - `DISCORD_TOKEN`: Your Discord bot token
  - `DATABASE_URL`: Your PostgreSQL connection string

#### Web Dashboard (Web Service)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT wsgi:app`
- **Environment Variables**:
  - `PYTHON_VERSION`: 3.11.0
  - `SESSION_SECRET`: Generate a secure random string
  - `DATABASE_URL`: Your PostgreSQL connection string

## Security Considerations

This bot implementation includes:
- Security headers to prevent common web vulnerabilities
- Database IP restrictions to limit access
- Secure session management
- Proper environment variable configuration

## Local Development

### Requirements
- Python 3.11+
- PostgreSQL database
- Discord Bot Token
- Dependencies in requirements.txt

### Setup
1. Clone this repository
2. Create a `.env` file based on `.env.example`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the bot with one of these options:
   - Standard startup: `python main.py`
   - Fast startup: `bash start_fast.sh` or `python fast_bot.py`

### Optimized Performance
This bot includes performance optimizations:
- `fast_bot.py` for rapid Discord login (~0.7s connection time)
- Delayed database initialization after bot is already online
- Optimized intents configuration for faster startup
- `start_fast.sh` with performance flags enabled

## License

This project is licensed under the MIT License - see the LICENSE file for details.