import discord
from discord.ext import commands, tasks
from discord import app_commands
import sys
import os
import json
import asyncio
import random
import traceback
import string
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ollama_client import OllamaClient
from core.subconscious import Subconscious
from core.autonomy import AutonomyManager
from core.memory_manager import MemoryManager
from core.advanced_tasks import AdvancedTasks
from utils.message_handler import send_split_message

class CompanionCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Checks if the bot is online.")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Pong! 🏓 ({round(self.bot.latency * 1000)}ms)")

    @app_commands.command(name="diary", description="Read Lumi's latest private diary entry about you.")
    async def diary(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        entry = self.bot.memory_manager.read_latest_diary(user_id)
        if entry:
            await interaction.response.send_message(f"📔 **Lumi's Secret Diary**\n\n*{entry}*", ephemeral=True)
        else:
            await interaction.response.send_message("❌ She hasn't written a diary entry about you yet! Give her a few days to dream.", ephemeral=True)

    @app_commands.command(name="watch", description="Give Lumi a YouTube link to roast asynchronously.")
    async def watch(self, interaction: discord.Interaction, url: str):
        user_id = str(interaction.user.id)
        await interaction.response.send_message("Ugh, fine. Added to my queue. Give me a few minutes to watch it. 🙄")
        asyncio.create_task(self.bot.advanced_tasks.process_youtube_video(url, user_id, interaction.channel))

    @app_commands.command(name="engagement", description="Toggle whether Lumi can text you first in DMs.")
    async def engagement(self, interaction: discord.Interaction, toggle: bool):
        user_id = str(interaction.user.id)
        profile = self.bot.memory_manager.get_user_profile(user_id)
        profile['engagement_enabled'] = toggle
        self.bot.memory_manager.save_user_profile(user_id, profile)
        state = "ON" if toggle else "OFF"
        await interaction.response.send_message(f"✨ Proactive DM engagement is now **{state}**.", ephemeral=True)

    @app_commands.command(name="status", description="Shows her current mood and relationship with you.")
    async def status(self, interaction: discord.Interaction):
        try:
            with open(os.path.join("data", "character_card.json"), 'r', encoding='utf-8') as f:
                card = json.load(f)
            
            user_id = str(interaction.user.id)
            user_profile = self.bot.memory_manager.get_user_profile(user_id)
            state = user_profile.get('dynamic_state', {})
            
            msg = (
                f"**🧠 {card['core_identity']['name']} Status for you**\n"
                f"Your Vibe (Her Mood): {state.get('mood')} | Energy: {state.get('energy')} | Stress: {state.get('stress')}\n"
                f"Relationship with {user_profile.get('associated_name')}: Level {user_profile.get('intimacy_level')}\n"
            )
            await interaction.response.send_message(msg)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

class CompanionBot(commands.Bot):
    def __init__(self, config):
        intents = discord.Intents.default()
        intents.messages = True
        intents.guild_messages = True
        intents.dm_messages = True
        intents.message_content = True
        super().__init__(command_prefix=config['discord']['command_prefix'], intents=intents)
        self.config = config
        self.ollama = OllamaClient(config)
        self.subconscious = Subconscious(config)
        self.memory_manager = MemoryManager()
        
        self.short_term_memory = {}
        self.message_buffers = {}
        self.buffer_tasks = {}
        
        self.autonomy = None 
        self.advanced_tasks = None

    async def setup_hook(self):
        await self.add_cog(CompanionCommands(self))
        await self.tree.sync()
        print("✅ Slash commands synchronized.")

    async def simulate_typing_delay(self, message_content, user_id):
        user_profile = self.memory_manager.get_user_profile(user_id)
        energy = user_profile.get('dynamic_state', {}).get('energy', 50)
        base_delay = 2.0 if energy > 60 else 4.5
        delay = max(1.0, base_delay - (len(message_content) / 200))
        await asyncio.sleep(delay)

    def apply_emotional_formatting(self, text, user_id):
        profile = self.memory_manager.get_user_profile(user_id)
        state = profile.get('dynamic_state', {})
        mood = state.get('mood', 50)
        energy = state.get('energy', 50)
        stress = state.get('stress', 0)

        if energy >= 80:
            return text.upper()
        elif mood <= 30 or stress >= 70:
            return text.lower().translate(str.maketrans('', '', string.punctuation)) + "..."
        return text

    async def process_buffered_messages(self, message, user_id, interrupted=False):
        try:
            channel = message.channel
            channel_id = str(channel.id)
            await asyncio.sleep(5.0) 
            
            if not self.message_buffers.get(user_id):
                return

            combined_text = " ".join(self.message_buffers[user_id])
            self.message_buffers[user_id] = []
            
            if not combined_text.strip():
                combined_text = "*looks at you silently*"

            is_new_user = self.update_last_interaction(user_id, channel)
            user_profile = self.memory_manager.get_user_profile(user_id)
            user_alias = user_profile.get('associated_name', 'Stranger')

            if channel_id not in self.short_term_memory:
                self.short_term_memory[channel_id] = []
                
            self.short_term_memory[channel_id].append({"role": user_alias, "content": combined_text})
            relevant = await asyncio.to_thread(self.memory_manager.recall_memories, combined_text, user_id)
            
            async with channel.typing():
                response = await asyncio.to_thread(
                    self.ollama.generate_response, 
                    combined_text, 
                    self.short_term_memory[channel_id], 
                    relevant, 
                    user_alias, 
                    user_id,
                    is_new_user,
                    interrupted
                )
                
                if not response or not str(response).strip():
                    response = "*(Stares blankly, lost in thought...)*"

                await self.simulate_typing_delay(response, user_id)
            
            formatted_response = self.apply_emotional_formatting(response, user_id)

            self.short_term_memory[channel_id].append({"role": "Lumi", "content": formatted_response})
            if len(self.short_term_memory[channel_id]) > 20: 
                self.short_term_memory[channel_id] = self.short_term_memory[channel_id][-20:]
                
            asyncio.create_task(asyncio.to_thread(self.memory_manager.save_memory, user_alias, combined_text, user_id))
            asyncio.create_task(asyncio.to_thread(self.memory_manager.save_memory, "Lumi", formatted_response, user_id))
            
            await send_split_message(channel, formatted_response, reply_to=message)
            asyncio.create_task(asyncio.to_thread(self.subconscious.analyze_interaction, list(self.short_term_memory[channel_id]), user_id, user_alias))
            
        except Exception as e:
            print(f"🚨 [CRITICAL ERROR] Failed to process message buffer: {e}")
            traceback.print_exc()

    async def on_ready(self):
        print(f'✅ Logged in as {self.user}')
        if not self.autonomy: self.autonomy = AutonomyManager(self, self.config)
        if not self.advanced_tasks: self.advanced_tasks = AdvancedTasks(self, self.config)

    def update_last_interaction(self, user_id, channel):
        try:
            profile = self.memory_manager.get_user_profile(user_id)
            is_new = profile.get("last_interaction") == ""
            profile["last_interaction"] = datetime.now().isoformat()
            if isinstance(channel, discord.DMChannel):
                profile["last_dm_id"] = str(channel.id)
            self.memory_manager.save_user_profile(user_id, profile)
            return is_new
        except Exception as e:
            print(f"Timestamp Update Error: {e}")
            return False

    async def on_message(self, message):
        try:
            if message.author == self.user or message.author.bot: return
            
            is_dm = isinstance(message.channel, discord.DMChannel)
            is_mentioned = self.user in message.mentions
            
            if not is_dm and not is_mentioned:
                return

            user_id = str(message.author.id)
            channel_id = str(message.channel.id)
            content = message.content.replace(f'<@{self.user.id}>', '').strip()
            
            if channel_id not in self.short_term_memory:
                self.short_term_memory[channel_id] = []
                
            if user_id not in self.message_buffers:
                self.message_buffers[user_id] = []
                
            self.message_buffers[user_id].append(content if content else "*looks at you silently*")
            
            interrupted = False
            if user_id in self.buffer_tasks and not self.buffer_tasks[user_id].done():
                self.buffer_tasks[user_id].cancel()
                interrupted = True
                
            self.buffer_tasks[user_id] = asyncio.create_task(self.process_buffered_messages(message, user_id, interrupted))
            
        except Exception as e:
            print(f"🚨 [CRITICAL ERROR] Failed in on_message: {e}")
            traceback.print_exc()
