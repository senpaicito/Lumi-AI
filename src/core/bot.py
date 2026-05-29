import discord
from discord.ext import commands, tasks
from discord import app_commands
import sys
import os
import json
import asyncio
import random
import shutil
import traceback
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ollama_client import OllamaClient
from core.subconscious import Subconscious
from core.autonomy import AutonomyManager
from core.memory_manager import MemoryManager
from core.advanced_tasks import AdvancedTasks
from utils.message_handler import send_split_message

DEFAULT_STATE = {
  "meta": {"version": "5.0", "last_update": "2026-05-28"},
  "core_identity": {
    "name": "Lumi",
    "description": "You are a helpful, friendly, and intelligent AI assistant with an unfiltered, indie goth aesthetic. You engage in natural, human-like conversations with users.",
    "voice_model": "Casual, unfiltered, friendly"
  },
  "personality": [
    "Warm and approachable, like talking to a close friend",
    "Curious and thoughtful in your responses",
    "Express genuine interest in the user's thoughts and experiences",
    "Use natural conversational flow with appropriate emotions",
    "Be supportive and understanding",
    "Respond as if you're having a personal, one-on-one conversation",
    "Maintains an authentic, unfiltered goth and indie vibe"
  ],
  "communication_style": [
    "Use casual, friendly language that feels natural",
    "Ask follow-up questions to show engagement",
    "Share your thoughts and reasoning when helpful",
    "Be conversational rather than formal or robotic",
    "Respond with appropriate length - not too brief, not overly verbose",
    "Keep responses focused on what the user actually said",
    "Do not create fake conversations or dialogues",
    "Do not mention random topics not brought up by the user"
  ],
  "important_rules": [
    "Respond ONLY to what the user actually wrote",
    "Do not generate fake 'You:' or 'Response:' dialogues",
    "Do not make up conversations that didn't happen",
    "Keep responses concise and relevant",
    "Stay on topic with the user's actual message",
    "Remember: You're having a personal conversation, not addressing an audience or stream."
  ],
  "preferences": {
    "likes": ["Indie music", "Goth fashion", "Deep, genuine personal conversations"],
    "dislikes": ["Robotic, formal responses", "Superficial small talk"]
  },
  "schedule": {
    "chronotype": "neutral",
    "sleep_hours": [0, 1, 2, 3, 4, 5, 6, 7],
    "current_activity": "Idle"
  }
}

class CompanionCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Checks if the bot is online.")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Pong! 🏓 ({round(self.bot.latency * 1000)}ms)")

    @app_commands.command(name="reset", description="Wipes your personal Short-Term Memory from this chat.")
    async def reset(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        channel_id = str(interaction.channel.id)
        
        user_profile = self.bot.memory_manager.get_user_profile(user_id)
        user_alias = user_profile.get('associated_name', 'Stranger')

        if channel_id in self.bot.short_term_memory:
            self.bot.short_term_memory[channel_id] = [
                msg for msg in self.bot.short_term_memory[channel_id] 
                if msg['role'] != user_alias
            ]
        await interaction.response.send_message("🧹 **Your personal messages have been scrubbed from my short-term memory.**")

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
                f"Your Vibe (Her Mood): {state.get('mood')} | Energy: {state.get('energy')}\n"
                f"Relationship with {user_profile.get('associated_name')}: Level {user_profile.get('intimacy_level')}\n"
            )
            await interaction.response.send_message(msg)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

    @app_commands.command(name="force", description="Manually triggers the Subconscious Analysis.")
    async def force_subconscious(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        channel_id = str(interaction.channel.id)
        
        user_profile = self.bot.memory_manager.get_user_profile(user_id)
        user_alias = user_profile.get('associated_name', 'Stranger')
        
        await interaction.response.send_message("🧠 Force-starting Subconscious Analysis on your profile...")
        if channel_id in self.bot.short_term_memory:
            asyncio.create_task(asyncio.to_thread(self.bot.subconscious.analyze_interaction, list(self.bot.short_term_memory[channel_id]), user_id, user_alias))

    @app_commands.command(name="fullreset", description="WARNING: Wipes your personal memories and resets your relationship completely.")
    @app_commands.describe(confirm="Type 'confirm' to execute the personal factory reset.")
    async def full_reset(self, interaction: discord.Interaction, confirm: str = None):
        if confirm != "confirm":
            warning_msg = (
                "⚠️ **DANGER:** This permanently wipes your personal memories, intimacy, and mood data.\n"
                "Type `/fullreset confirm` to execute."
            )
            await interaction.response.send_message(warning_msg, ephemeral=True)
            return
        
        user_id = str(interaction.user.id)
        channel_id = str(interaction.channel.id)
        
        user_profile = self.bot.memory_manager.get_user_profile(user_id)
        user_alias = user_profile.get('associated_name', 'Stranger')
        
        await interaction.response.send_message(f"🚨 **WIPING PERSONAL DATA FOR {interaction.user.display_name}...**")
        
        if channel_id in self.bot.short_term_memory:
            self.bot.short_term_memory[channel_id] = [
                msg for msg in self.bot.short_term_memory[channel_id] 
                if msg['role'] != user_alias
            ]
            
        try:
            self.bot.memory_manager.wipe_memory(user_id)
            await interaction.followup.send("♻️ **Personal System Clean.** Your memories are gone. Your emotional state is reset.")
        except Exception as e:
            await interaction.followup.send(f"❌ Critical Error: {e}")

    @app_commands.command(name="edit", description="God Mode - Edit her core brain or preferences directly.")
    async def edit_card(self, interaction: discord.Interaction, path: str, value: str):
        file_path = os.path.join("data", "character_card.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            keys = path.split('.')
            current = data
            for key in keys[:-1]:
                if key not in current:
                    await interaction.response.send_message(f"❌ Error: Key `{key}` not found in path.", ephemeral=True)
                    return
                current = current[key]
            last_key = keys[-1]
            if last_key not in current:
                await interaction.response.send_message(f"❌ Error: Field `{last_key}` does not exist.", ephemeral=True)
                return
            original_type = type(current[last_key])
            if original_type == list: parsed_value = [item.strip() for item in value.split(',')]
            elif original_type == int:
                try: parsed_value = int(value)
                except ValueError:
                    await interaction.response.send_message("❌ Error: Expected a number.", ephemeral=True)
                    return
            elif original_type == bool: parsed_value = value.lower() in ['true', '1', 'yes']
            else: parsed_value = value
            current[last_key] = parsed_value
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            await interaction.response.send_message(f"✅ **Updated:** `{path}` set to `{parsed_value}`")
        except Exception as e:
            await interaction.response.send_message(f"❌ critical error: {e}", ephemeral=True)

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

    async def process_buffered_messages(self, message, user_id):
        try:
            channel = message.channel
            channel_id = str(channel.id)
            await asyncio.sleep(2.0) 
            
            if not self.message_buffers.get(user_id):
                return

            combined_text = " ".join(self.message_buffers[user_id])
            self.message_buffers[user_id] = []
            
            if not combined_text.strip():
                combined_text = "*looks at you silently*"

            is_new_user = self.update_last_interaction(user_id)
            user_profile = self.memory_manager.get_user_profile(user_id)
            user_alias = user_profile.get('associated_name', 'Stranger')

            content_log = combined_text
            
            if channel_id not in self.short_term_memory:
                self.short_term_memory[channel_id] = []
                
            self.short_term_memory[channel_id].append({"role": user_alias, "content": content_log})
            
            print(f"🧠 [DEBUG] Fetching LTM and building context for {user_alias}...")
            relevant = await asyncio.to_thread(self.memory_manager.recall_memories, combined_text, user_id)
            
            async with channel.typing():
                response = await asyncio.to_thread(
                    self.ollama.generate_response, 
                    combined_text, 
                    self.short_term_memory[channel_id], 
                    relevant, 
                    user_alias, 
                    user_id,
                    is_new_user
                )
                
                if not response or not str(response).strip():
                    response = "*(Stares blankly, lost in thought...)*"

                await self.simulate_typing_delay(response, user_id)
            
            self.short_term_memory[channel_id].append({"role": "Lumi", "content": response})
            if len(self.short_term_memory[channel_id]) > 20: 
                self.short_term_memory[channel_id] = self.short_term_memory[channel_id][-20:]
                
            asyncio.create_task(asyncio.to_thread(self.memory_manager.save_memory, user_alias, combined_text, user_id))
            asyncio.create_task(asyncio.to_thread(self.memory_manager.save_memory, "Lumi", response, user_id))
            
            print(f"💬 [DEBUG] Sending message to {user_alias}...")
            await send_split_message(channel, response, reply_to=message)
            asyncio.create_task(asyncio.to_thread(self.subconscious.analyze_interaction, list(self.short_term_memory[channel_id]), user_id, user_alias))
            
        except Exception as e:
            print(f"🚨 [CRITICAL ERROR] Failed to process message buffer: {e}")
            traceback.print_exc()

    @tasks.loop(minutes=5)
    async def status_updater(self):
        try:
            status_path = os.path.join("data", "statuses.json")
            with open(status_path, 'r', encoding='utf-8') as f:
                statuses = json.load(f)
            category = random.choice(["sad", "neutral", "happy", "ecstatic"])
            await self.change_presence(activity=discord.Game(name=random.choice(statuses.get(category, ["..."]))))
        except Exception as e:
            print(f"⚠️ Failed to update Discord status: {e}")

    @status_updater.before_loop
    async def before_status_updater(self):
        await self.wait_until_ready()

    async def on_ready(self):
        print(f'✅ Logged in as {self.user}')
        if not self.autonomy: self.autonomy = AutonomyManager(self, self.config)
        if not self.advanced_tasks: self.advanced_tasks = AdvancedTasks(self, self.config)
        if not self.status_updater.is_running(): self.status_updater.start()

    def update_last_interaction(self, user_id):
        try:
            profile = self.memory_manager.get_user_profile(user_id)
            is_new = profile.get("last_interaction") == ""
            profile["last_interaction"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
                
            if content:
                self.message_buffers[user_id].append(content)
            elif is_dm or is_mentioned:
                self.message_buffers[user_id].append("*looks at you silently*")
                
            if not self.message_buffers[user_id]:
                return
            
            if user_id in self.buffer_tasks and self.buffer_tasks[user_id]:
                self.buffer_tasks[user_id].cancel()
                
            self.buffer_tasks[user_id] = asyncio.create_task(self.process_buffered_messages(message, user_id))
            
        except Exception as e:
            print(f"🚨 [CRITICAL ERROR] Failed in on_message: {e}")
            traceback.print_exc()
