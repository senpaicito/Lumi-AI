import asyncio
from datetime import datetime, timedelta
import random
import json
import os
from discord.ext import tasks

class AutonomyManager:
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.ollama = bot.ollama
        self.card_path = os.path.join("data", "character_card.json")
        self.heartbeat.start()

    def get_last_interaction(self):
        try:
            with open(self.card_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # FIX: V3.0 uses 'relationship_depth'
                if 'relationship_depth' in data:
                    timestamp_str = data['relationship_depth'].get('last_interaction', "2000-01-01 00:00:00")
                    return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except:
            pass
        return datetime.now()

    @tasks.loop(seconds=60)
    async def heartbeat(self):
        if not self.config['autonomy']['enabled']: return

        now = datetime.now()
        start_hour = self.config['autonomy']['wake_hour']
        end_hour = self.config['autonomy']['sleep_hour']
        if not (start_hour <= now.hour < end_hour): return

        last_seen = self.get_last_interaction()
        delta = now - last_seen
        min_silence = self.config['autonomy']['min_silence_hours_before_initiate']
        
        if delta < timedelta(hours=min_silence): return

        chance = self.config['autonomy']['initiate_chance']
        if random.random() > chance: return

        print("⚡ Autonomy Triggered")
        user_id = self.config['discord']['allowed_user_id']
        user = self.bot.get_user(user_id)
        
        if user:
            message_content = await self.bot.loop.run_in_executor(None, self.ollama.generate_initiative)
            try:
                await user.send(message_content)
                self.bot.short_term_memory.append({"role": "Gemma", "content": message_content})
                self.update_timestamp()
            except Exception as e:
                print(f"Failed to send autonomy message: {e}")

    def update_timestamp(self):
        try:
            with open(self.card_path, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                # FIX: V3.0 uses 'relationship_depth'
                if 'relationship_depth' in data:
                    data['relationship_depth']['last_interaction'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.seek(0)
                    json.dump(data, f, indent=2)
                    f.truncate()
        except Exception as e:
            print(f"Error updating timestamp: {e}")

    @heartbeat.before_loop
    async def before_heartbeat(self):
        await self.bot.wait_until_ready()