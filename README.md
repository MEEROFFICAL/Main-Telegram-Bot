
# HYPER SKINS BOT

A Telegram bot for customizing PUBG Mobile skins and X-suits.

## Features
- Custom skin creation
- Multiple skin mixing
- X-suit customization
- Admin controls
- User approval system

## Setup
1. Install requirements: `pip install -r requirements.txt`
2. Create `items.csv` with skin IDs and names
3. Set your bot token in the `TOKEN` variable
4. Run the bot: `python main.py`

## Commands
- `/skin <real_id> <mod_id>` - Create custom skin
- `/multiskin <real> <mod> <real> <mod>` - Mix multiple skins
- `/xsuits <real_id> <mod_id>` - Customize X-Suits

## Admin Commands
- `/approve <user_id>` - Approve user
- `/disapprove <user_id>` - Remove user access
- `/broadcast <message>` - Send message to all users
- `/users` - List all users
