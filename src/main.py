import json
import os
import sys

# Ensure src is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.bot import CompanionBot

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("CRITICAL ERROR: config.json not found in root directory!")
        sys.exit(1)

def main():
    config = load_config()
    
    if config['discord']['bot_token'] == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print("⚠️ ERROR: Please update config.json with your actual Discord Token.")
        return

    bot = CompanionBot(config)
    
    try:
        bot.run(config['discord']['bot_token'])
    except Exception as e:
        print(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()