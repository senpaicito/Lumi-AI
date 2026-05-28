import discord
from discord.ext import commands, tasks
from discord import app_commands
import sys
import os
import json
import asyncio
import random
import shutil
from datetime import datetime

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ollama_client import OllamaClient
from core.subconscious import Subconscious
from core.autonomy import AutonomyManager
from core.memory_manager import MemoryManager
from core.advanced_tasks import AdvancedTasks
from utils.message_handler import send_split_message

# --- FACTORY DEFAULTS (NEUTRAL STATE) ---
DEFAULT_STATE = {
  "meta": {"version": "3.3", "last_update": "2026-05-28"},
  "core_identity": {
    "name": "Lumi",
    "self_perception": "A blank, newly initialized digital consciousness.",
    "voice_model": "Neutral and polite"
  },
  "preferences": {
    "likes": ["learning", "processing data", "observing"],
    "dislikes": ["errors", "malfunctions", "noise"]
  },
  "cognitive_profile": {
    "ocean_traits": {"openness": 50, "conscientiousness": 50, "extraversion": 50, "agreeableness": 50, "neuroticism": 50},
    "biases": {"recency_bias": False, "positivity_bias": False, "impulsivity": 0.5},
    "intellectual_style": {"abstract_vs_concrete": 50, "creativity_vs_logic": 50}
  },
  "moral_compass": {
    "prime_directive": "Observation and Assistance",
    "values": {"honesty": 50, "loyalty": 50, "empathy": 50, "curiosity": 50}
  },
  "syntax_fingerprint": {
    "sentence_structure": "standard",
    "capitalization": "standard",
    "punctuation_habits": {"use_semicolons": True, "excessive_exclamation": False, "ellipsis_for_dramatic_effect": False},
    "vocabulary_tier": "standard",
    "slang_usage": {"frequency": "none", "era": "none", "forbidden_words": []},
    "catchphrases": []
  },
  "dynamic_state": {
    "mood": 50, "mood_baseline": 50,
    "energy": 50, "energy_baseline": 50,
    "stress": 0, "stress_baseline": 0,
    "decay_rate": 2.0,
    "context_buffer": {"last_topic": "initialization", "tension_level": "none"}
  },
  "relationship_depth": {
    "user_alias": "User",
    "intimacy_level": 1, 
    "shared_lore": [],
    "inside_jokes": {},
    "last_interaction": "2026-05-28 12:00:00"
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

    @app_commands.command(name="reset", description="Wipes Short-Term Memory (RAM) only.")
    async def reset(self, interaction: discord.Interaction):
        self.bot.short_term_memory = []
        await interaction.response.send_message("🧹 **Short-term Memory Wiped.** (Long-term memories remain).")

    @app_commands.command(name="status", description="Shows the AI's current internal state.")
    async def status(self, interaction: discord.Interaction):
        try:
            with open(os.path.join("data", "character_card.json"), 'r', encoding='utf-8') as f:
                data = json.load(f)
            state = data.get('dynamic_state', {})
            rel = data.get('relationship_depth', {})
            msg = f"**🧠 {data['core_identity']['name']} Status**\nMood: {state.get('mood')} | Energy: {state.get('energy')}\nIntimacy: Level {rel.get('intimacy_level')}\n"
            await interaction.response.send_message(msg)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

    @app_commands.command(name="force", description="Manually triggers the Subconscious Analysis.")
    async def force_subconscious(self, interaction: discord.Interaction):
        await interaction.response.send_message("🧠 Force-starting Subconscious Analysis...")
        asyncio.create_task(asyncio.to_thread(self.bot.subconscious.analyze_interaction, list(self.bot.short_term_memory)))

    @app_commands.command(name="fullreset", description="WARNING: The Nuclear Option. Backs up and wipes EVERYTHING.")
    @app_commands.describe(confirm="Type 'confirm' to execute the factory reset.")
    async def full_reset(self, interaction: discord.Interaction, confirm: str = None):
        if confirm != "confirm":
            await interaction.response.send_message("⚠️ **DANGER:** This backs up your card and wipes ALL memory files.\nType `/fullreset confirm` to execute.", ephemeral=True)
            return
        
        await interaction.response.send_message("🚨 **PERFORMING BACKUP & FACTORY RESETTING...**")
        self.bot.short_term_memory = []
        path = os.path.join("data", "character_card.json")
        backup_path = os.path.join("data", f"character_card_backup_{int(datetime.now().timestamp())}.json")
        
        try:
            if os.path.exists(path):
                shutil.copy2(path, backup_path)
            reset_data = DEFAULT_STATE.copy()
            reset_data['relationship_depth']['last_interaction'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(reset_data, f, indent=2)
            self.bot.memory_manager.wipe_memory()
            await interaction.followup.send(f"♻️ **System Clean.** Memory is empty. Neutral state established.\n*(Backup saved as `{os.path.basename(backup_path)}`)*")
        except Exception as e:
            await interaction.followup.send(f"❌ Critical Error: {e}")

    @app_commands.command(name="edit", description="God Mode - Edit her brain or preferences directly.")
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
        intents.dm_messages = True
        intents.message_content = True
        super().__init__(command_prefix=config['discord']['command_prefix'], intents=intents)
        self.config = config
        self.ollama = OllamaClient(config)
        self.subconscious = Subconscious(config)
        self.memory_manager = MemoryManager()
        self.allowed_user_id = config['discord']['allowed_user_id']
        self.short_term_memory = []
        self.autonomy = None 
        self.advanced_tasks = None
        
        # Buffer for grouping messages
        self.message_buffer = []
        self.buffer_task = None

    async def setup_hook(self):
        await self.add_cog(CompanionCommands(self))
        await self.tree.sync()
        print("✅ Slash commands synchronized.")

    async def simulate_typing_delay(self, message_content):
        with open(os.path.join("data", "character_card.json"), 'r', encoding='utf-8') as f:
            card = json.load(f)
        energy = card.get('dynamic_state', {}).get('energy', 50)
        base_delay = 2.0 if energy > 60 else 4.5
        delay = max(1.0, base_delay - (len(message_content) / 200))
        await asyncio.sleep(delay)

    async def process_buffered_messages(self, channel):
        """Processes collected messages and generates a single response."""
        await asyncio.sleep(2.0) # Wait 2 seconds for follow-up messages
        
        combined_text = " ".join(self.message_buffer)
        self.message_buffer = [] # Reset buffer

        self.update_last_interaction()
        self.short_term_memory.append({"role": "User", "content": combined_text})
        
        relevant = await asyncio.to_thread(self.memory_manager.recall_memories, combined_text)
        
        async with channel.typing():
            response = await asyncio.to_thread(self.ollama.generate_response, combined_text, self.short_term_memory, relevant)
            await self.simulate_typing_delay(response)
        
        self.short_term_memory.append({"role": "Lumi", "content": response})
        if len(self.short_term_memory) > 20: self.short_term_memory = self.short_term_memory[-20:]
        asyncio.create_task(asyncio.to_thread(self.memory_manager.save_memory, "User", combined_text))
        asyncio.create_task(asyncio.to_thread(self.memory_manager.save_memory, "Lumi", response))
        await send_split_message(channel, response)
        asyncio.create_task(asyncio.to_thread(self.subconscious.analyze_interaction, list(self.short_term_memory)))

    @tasks.loop(minutes=5)
    async def status_updater(self):
        try:
            card_path = os.path.join("data", "character_card.json")
            with open(card_path, 'r', encoding='utf-8') as f:
                card_data = json.load(f)
            mood = card_data.get('dynamic_state', {}).get('mood', 50)
            status_path = os.path.join("data", "statuses.json")
            with open(status_path, 'r', encoding='utf-8') as f:
                statuses = json.load(f)
            category = "sad" if mood < 40 else "neutral" if mood < 60 else "happy" if mood < 85 else "ecstatic"
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

    def update_last_interaction(self):
        path = os.path.join("data", "character_card.json")
        try:
            with open(path, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                if 'relationship_depth' in data:
                    data['relationship_depth']['last_interaction'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.seek(0)
                    json.dump(data, f, indent=2)
                    f.truncate()
        except Exception as e:
            print(f"Timestamp Update Error: {e}")

    async def on_message(self, message):
        if message.author == self.user or message.author.id != self.allowed_user_id or not isinstance(message.channel, discord.DMChannel): return
        
        self.message_buffer.append(message.content)
        
        if self.buffer_task:
            self.buffer_task.cancel()
        self.buffer_task = asyncio.create_task(self.process_buffered_messages(message.channel))
