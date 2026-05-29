import requests
import json
import os
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
            return {}

    def _get_user_profile(self, user_id):
        file_path = os.path.join("data", "memory", f"{user_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"associated_name": "Stranger", "intimacy_level": 1, "dynamic_state": {"mood": 50, "energy": 50}}

    def _build_full_psyche_prompt(self, card, user_alias, user_id):
        identity = card.get('core_identity', {})
        prompt = f"You are {identity.get('name', 'Lumi')}. {identity.get('description', '')}\n"

        if 'personality' in card:
            prompt += "Personality:\n" + "\n".join(f"- {p}" for p in card['personality']) + "\n\n"
            
        user_data = self._get_user_profile(user_id)
        state = user_data.get('dynamic_state', {})
        mood = state.get('mood', 50)
        
        if mood > 80: prompt += "Mood: You are euphoric and high-energy with this user! 🌟\n"
        elif mood < 30: prompt += "Mood: You are feeling sad, guarded, and low-energy with this user.\n"
        
        prompt += f"\nCRITICAL CONTEXT: You are currently replying DIRECTLY to: {user_alias}.\n"
        return prompt

    def generate_response(self, user_input, history, relevant_memories, user_alias, user_id, is_new_user=False, interrupted=False):
        card = self.load_character_card()
        system_prompt = self._build_full_psyche_prompt(card, user_alias, user_id)
        
        memory_block = ""
        if relevant_memories:
            memory_list = "\n".join(relevant_memories)
            memory_block = f"\nRELEVANT PAST MEMORIES WITH {user_alias.upper()}:\n{memory_list}\n"

        context = ""
        for msg in history[-15:]: 
            context += f"{msg['role']}: {msg['content']}\n"
            
        full_prompt = f"{system_prompt}{memory_block}\nCONVERSATION HISTORY:\n{context}"
        
        if interrupted:
            full_prompt += "\n[SYSTEM ALERT: The user just interrupted you / double-texted! React accordingly based on your current stress and energy!]\n"
            
        full_prompt += f"\n{card.get('core_identity', {}).get('name', 'Lumi')}:"

        payload = {"model": self.model, "prompt": full_prompt, "stream": False, "options": {"temperature": 0.85}}
        try:
            response = requests.post(self.api_url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json().get('response', '').strip()
        except Exception as e:
            return f"Oops, my brain just short-circuited... [Internal Error: {str(e)}]"
