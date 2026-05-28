import sys
import os
import json
import asyncio
import threading
from datetime import datetime

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ollama_client import OllamaClient
from core.subconscious import Subconscious
from core.memory_manager import MemoryManager

# --- COLORS FOR TERMINAL ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class CLIInterface:
    def __init__(self):
        self.config = self.load_config()
        self.ollama = OllamaClient(self.config)
        self.subconscious = Subconscious(self.config)
        self.memory_manager = MemoryManager()
        self.short_term_memory = []
        self.user_name = "Admin"

    def load_config(self):
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except:
            print("❌ Could not load config.json")
            sys.exit(1)

    def print_banner(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Colors.HEADER}==========================================")
        print(f"      PROJECT COMPANION - CLI LINK")
        print(f"=========================================={Colors.ENDC}")
        print(f"{Colors.WARNING}Type 'quit' to exit. Type '!status' for stats.{Colors.ENDC}\n")

    def run(self):
        self.print_banner()
        
        # Main Loop
        while True:
            try:
                user_input = input(f"{Colors.GREEN}You: {Colors.ENDC}")
                if not user_input.strip():
                    continue

                if user_input.lower() in ['quit', 'exit']:
                    print("👋 Disconnecting...")
                    break

                # Handle Commands
                if user_input.startswith("!"):
                    self.handle_command(user_input)
                    continue

                # Process Chat
                self.process_chat(user_input)

            except KeyboardInterrupt:
                print("\n👋 Disconnecting...")
                break

    def process_chat(self, user_input):
        # 1. Memory
        self.short_term_memory.append({"role": "User", "content": user_input})
        
        # 2. Long Term Retrieval
        relevant_memories = self.memory_manager.recall_memories(user_input)
        
        print(f"{Colors.CYAN}Gemma is thinking...{Colors.ENDC}", end="\r")

        # 3. Generate
        response = self.ollama.generate_response(
            user_input, 
            self.short_term_memory, 
            relevant_memories
        )

        # 4. Output
        # Clear the "thinking" line
        print(" " * 20, end="\r")
        print(f"{Colors.BLUE}Gemma: {Colors.ENDC}{response}\n")

        # 5. Save & Update State
        self.short_term_memory.append({"role": "Gemma", "content": response})
        if len(self.short_term_memory) > 20:
            self.short_term_memory.pop(0)

        # Background saves (pseudo-async)
        threading.Thread(target=self.memory_manager.save_memory, args=("User", user_input)).start()
        threading.Thread(target=self.memory_manager.save_memory, args=("Gemma", response)).start()
        threading.Thread(target=self.subconscious.analyze_interaction, args=(list(self.short_term_memory),)).start()

    def handle_command(self, command):
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == "!status":
            self.show_status()
        elif cmd == "!edit":
            if len(parts) < 3:
                print(f"{Colors.FAIL}Usage: !edit path value{Colors.ENDC}")
                return
            path = parts[1]
            value = " ".join(parts[2:])
            self.edit_card(path, value)
        else:
            print(f"{Colors.FAIL}Unknown command.{Colors.ENDC}")

    def show_status(self):
        try:
            with open(os.path.join("data", "character_card.json"), 'r') as f:
                data = json.load(f)
            state = data.get('dynamic_state', {})
            print(f"\n{Colors.BOLD}[ STATUS REPORT ]{Colors.ENDC}")
            print(f"Mood: {state.get('mood')}")
            print(f"Energy: {state.get('energy')}")
            print(f"Obsession: {data.get('narrative_engine', {}).get('current_obsession')}\n")
        except:
            print("Error reading status.")

    def edit_card(self, path, value):
        # Re-using logic similar to the bot's edit command
        file_path = os.path.join("data", "character_card.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            keys = path.split('.')
            current = data
            for key in keys[:-1]:
                current = current[key]
            
            last_key = keys[-1]
            
            # Type conversion logic
            if value.lower() == 'true': value = True
            elif value.lower() == 'false': value = False
            elif value.isdigit(): value = int(value)
            
            current[last_key] = value

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"{Colors.GREEN}✅ Updated {path} to {value}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")

if __name__ == "__main__":
    cli = CLIInterface()
    cli.run()