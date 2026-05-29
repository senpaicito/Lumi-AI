import asyncio
import os
import json
from datetime import datetime

class AutonomyManager:
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.bot.loop.create_task(self.autonomy_loop())

    async def autonomy_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                now = datetime.now()
                # 1. REM Sleep Processing (e.g., 3 AM)
                if now.hour == 3 and now.minute < 10:
                    await self.bot.advanced_tasks.process_rem_sleep()
                    await asyncio.sleep(3600) 
                
                # 2. Proactive DM Engagement
                memory_dir = self.bot.memory_manager.memory_dir
                for filename in os.listdir(memory_dir):
                    if filename.endswith(".json") and filename != "diary":
                        user_id = filename.replace(".json", "")
                        profile = self.bot.memory_manager.get_user_profile(user_id)
                        
                        if profile.get("engagement_enabled") and profile.get("last_dm_id"):
                            last_time_str = profile.get("last_interaction")
                            if last_time_str:
                                last_time = datetime.fromisoformat(last_time_str)
                                diff_hours = (now - last_time).total_seconds() / 3600
                                
                                # If 4 hours have passed, send a message in DMs ONLY
                                if 4.0 <= diff_hours <= 4.2:
                                    user = self.bot.get_user(int(user_id))
                                    if user:
                                        prompt = f"You haven't spoken to {profile.get('associated_name')} in over 4 hours. Text them first. Be casual and organic."
                                        response = self.bot.ollama._send_request(prompt) 
                                        
                                        formatted = self.bot.apply_emotional_formatting(response, user_id)
                                        await user.send(formatted)
                                        
                                        profile["last_interaction"] = datetime.now().isoformat()
                                        self.bot.memory_manager.save_user_profile(user_id, profile)
                
            except Exception as e:
                print(f"Autonomy Error: {e}")
            await asyncio.sleep(300)
