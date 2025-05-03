# BloxBot Deployment Guide

This document provides the exact build and start commands for deploying the BloxBot on Render.

## Deployment Configuration

The BloxBot uses a two-service architecture on Render:

1. **Web Service** - Handles HTTP requests and web dashboard
2. **Worker Service** - Runs the Discord bot without exposing ports

## Build Command (Same for Both Services)

```
pip install -r requirements.txt
```

## Start Commands

### Web Service Start Command

```
gunicorn --bind 0.0.0.0:$PORT --workers=2 --threads=4 --worker-class=gthread wsgi:app
```

### Worker Service (Discord Bot) Start Command

```
bash start_fast.sh
```

## Environment Variables

Both services require these environment variables:

```
DATABASE_URL=postgresql://...  # Your PostgreSQL connection string
DISCORD_TOKEN=...              # Your Discord bot token
```

## Manual Deployment Steps

If you're deploying manually:

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables
4. Start web service: `gunicorn --bind 0.0.0.0:5000 wsgi:app`
5. Start bot service: `bash start_fast.sh`

## Monitoring

After deployment, verify that:
1. The web service responds to HTTP requests
2. The Discord bot shows as online in Discord
3. Commands like `/ping` and `/online` work immediately after startup

## Troubleshooting

If you encounter issues:
1. Check the logs in the Render dashboard
2. Verify all environment variables are set correctly
3. Ensure the database is accessible from the deployment environment