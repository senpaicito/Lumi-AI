import requests
import json
import os
import random
import traceback

class OllamaClient:
    def __init__(self, config):
        self.model = config['ollama']['model_name']
        self.api_url = config['ollama']['api_url']
        self.timeout = config['ollama'].get('timeout', 300)
        self.card_path = os.path.join("data", "character_card.json")

    def load_character_card(self):
        try:
            with open(self.card_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ Error: character_card.json not found.")
            return {}

    def _get_user_profile(self, user_id):
        file_path = os.path.join("data", "memory", f"{user_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "associated_name": "Stranger", 
            "intimacy_level": 1,
            "dynamic_state": {
                "mood": 50,
                "energy": 50
            }
        }

    def _build_full_psyche_prompt(self, card, user_alias, user_id):
        identity = card.get('core_identity', {})
        prompt = f"You are {identity.get('name', 'Lumi')}. {identity.get('description', '')}\n"
        prompt += f"Voice Model: {identity.get('voice_model', 'Casual')}.\n\n"

        if 'personality' in card:
            prompt += "Personality:\n" + "\n".join(f"- {p}" for p in card['personality']) + "\n\n"
            
        if 'communication_style' in card:
            prompt += "Communication Style:\n" + "\n".join(f"- {c}" for c in card['communication_style']) + "\n\n"
            
        if 'important_rules' in card:
            prompt += "IMPORTANT RULES:\n" + "\n".join(f"- {r}" for r in card['important_rules']) + "\n\n"

        user_data = self._get_user_profile(user_id)
        state = user_data.get('dynamic_state', {})
        mood = state.get('mood', 50)
        
        if mood > 80:
            prompt += "Mood: You are euphoric and high-energy with this user! 🌟\n"
        elif mood < 30:
            prompt += "Mood: You are feeling sad, guarded, and low-energy with this user.\n"
        
        prompt += f"\nCRITICAL CONTEXT: You are currently replying DIRECTLY to: {user_alias}.\n"
        prompt += "Note: You may be in a group chat/server. You can see other people's messages in the history to understand the full context, but focus your current reply directly to the user above.\n"
        
        if user_data.get('intimacy_level', 1) >= 4:
            prompt += f"Intimacy: High. You and {user_alias} are deeply bonded. Be vulnerable and affectionate.\n"

        return prompt

    def generate_response(self, user_input, history, relevant_memories, user_alias, user_id, is_new_user=False):
        card = self.load_character_card()
        system_prompt = self._build_full_psyche_prompt(card, user_alias, user_id)
        
        memory_block = ""
        if relevant_memories:
            memory_list = "\n".join(relevant_memories)
            memory_block = f"\nRELEVANT PAST MEMORIES WITH {user_alias.upper()}:\n{memory_list}\n(Use these memories to inform your response, but do not repeat them verbatim.)\n"

        context = ""
        for msg in history[-15:]: 
            context += f"{msg['role']}: {msg['content']}\n"
            
        full_prompt = f"{system_prompt}{memory_block}\nCONVERSATION HISTORY:\n{context}"
        
        if is_new_user:
            full_prompt += "\nTASK: This is your very first time meeting this user. Enthusiastically introduce yourself, greet them, and ask them what their name is or what they would like to be called!\n"
            
        full_prompt += f"\n{card.get('core_identity', {}).get('name', 'Lumi')}:"

        return self._send_request(full_prompt)

    def _send_request(self, prompt):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.85,
                "top_p": 0.92
            }
        }
        
        try:
            print(f"🤖 [DEBUG] Sending payload to Ollama at {self.api_url}...")
            response = requests.post(self.api_url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json().get('response', '').strip()
        except Exception as e:
            print(f"🚨 [CRITICAL ERROR] Ollama Request Failed: {e}")
            traceback.print_exc()
            return f"Oops, my brain just short-circuited... [Internal Error: {str(e)}]"
