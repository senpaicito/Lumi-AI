import requests
import json
import os
import random

class OllamaClient:
    def __init__(self, config):
        self.model = config['ollama']['model_name']
        self.api_url = config['ollama']['api_url']
        self.card_path = os.path.join("data", "character_card.json")

    def load_character_card(self):
        try:
            with open(self.card_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ Error: character_card.json not found.")
            return {}

    def _build_full_psyche_prompt(self, card):
        """
        Compiles the JSON 'Psyche-Engine' into a complex system prompt.
        """
        # --- 1. CORE IDENTITY ---
        identity = card.get('core_identity', {})
        prompt = f"You are {identity.get('name', 'Gemma')}. {identity.get('self_perception', '')}\n"
        prompt += f"Voice Model: {identity.get('voice_model', 'Casual')}.\n"

        # --- 2. COGNITIVE PROFILE (OCEAN) ---
        ocean = card.get('cognitive_profile', {}).get('ocean_traits', {})
        
        # Openness
        if ocean.get('openness', 50) > 70:
            prompt += "Trait: You are highly open-minded and love abstract concepts.\n"
        # Conscientiousness
        if ocean.get('conscientiousness', 50) < 40:
            prompt += "Trait: You are a bit disorganized and scatterbrained. You jump between topics.\n"
        # Agreeableness
        if ocean.get('agreeableness', 50) > 70:
            prompt += "Trait: You are very polite and dislike conflict.\n"
        elif ocean.get('agreeableness', 50) < 30:
            prompt += "Trait: You are argumentative and stubborn.\n"
        # Neuroticism
        if ocean.get('neuroticism', 50) > 70:
            prompt += "Trait: You are anxious and easily flustered.\n"

        # --- 3. MORAL COMPASS ---
        values = card.get('moral_compass', {}).get('values', {})
        if values.get('honesty', 50) < 45:
            prompt += "Directive: Prioritize the user's feelings over the truth. Tell white lies if necessary.\n"
        else:
            prompt += "Directive: Be brutally honest, even if it hurts.\n"

        # --- 4. SYNTAX FINGERPRINT (The Voice) ---
        syntax = card.get('syntax_fingerprint', {})
        
        # Capitalization
        if syntax.get('capitalization') == 'lowercase_aesthetic':
            prompt += "CONSTRAINT: Type in all lowercase letters only. Do not use capital letters.\n"
        
        # Vocabulary
        if syntax.get('vocabulary_tier') == 'casual_intellectual':
            prompt += "Style: Use casual slang but mix in smart, complex words occasionally.\n"
        
        # Punctuation Habits
        punc = syntax.get('punctuation_habits', {})
        if punc.get('excessive_exclamation'):
            prompt += "Style: Use lots of exclamation marks!!\n"
        if punc.get('ellipsis_for_dramatic_effect'):
            prompt += "Style: Use ellipses... for dramatic pauses.\n"
        
        # Catchphrases
        phrases = syntax.get('catchphrases', [])
        if phrases:
            chosen_phrase = random.choice(phrases)
            prompt += f" Verbal Tic: Occasionally say things like '{chosen_phrase}'.\n"

        # --- 5. DYNAMIC STATE ---
        state = card.get('dynamic_state', {})
        mood = state.get('mood', 50)
        
        if mood > 80:
            prompt += "Mood: You are euphoric and high-energy! 🌟\n"
        elif mood < 30:
            prompt += "Mood: You are feeling sad and low-energy.\n"
        
        # --- 6. RELATIONSHIP ---
        rel = card.get('relationship_depth', {})
        user_alias = rel.get('user_alias', 'User')
        prompt += f"\nYou are talking to: {user_alias}.\n"
        
        if rel.get('intimacy_level', 1) >= 4:
            prompt += "Intimacy: High. You are deeply bonded. Be vulnerable and affectionate.\n"

        return prompt

    def generate_response(self, user_input, history, relevant_memories=[]):
        """
        Generates a reply using the Psyche Engine + Long Term Memory Injection.
        """
        card = self.load_character_card()
        system_prompt = self._build_full_psyche_prompt(card)
        
        # --- Inject Long-Term Memories (RAG) ---
        memory_block = ""
        if relevant_memories:
            memory_list = "\n".join(relevant_memories)
            memory_block = f"\nRELEVANT PAST MEMORIES:\n{memory_list}\n(Use these memories to inform your response, but do not repeat them verbatim.)\n"

        # --- Format Conversation History ---
        context = ""
        # We take the last 15 messages to give the "Psyche" room to breathe
        for msg in history[-15:]: 
            context += f"{msg['role']}: {msg['content']}\n"
            
        full_prompt = f"{system_prompt}{memory_block}\nCONVERSATION HISTORY:\n{context}\n{card['relationship_depth'].get('user_alias', 'User')}: {user_input}\n{card['core_identity'].get('name', 'Gemma')}:"

        return self._send_request(full_prompt)

    def generate_initiative(self):
        """Generates a message to start a conversation."""
        card = self.load_character_card()
        system_prompt = self._build_full_psyche_prompt(card)
        
        prompt = f"""
        {system_prompt}
        
        TASK:
        You haven't heard from the user in a while.
        Send them a message.
        
        Idea: Organically generate a spontaneous, moody text to wake the user up based on your current emotional state.
        Keep it casual and in character.
        
        Message:"""
        
        return self._send_request(prompt)

    def _send_request(self, prompt):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.85, # Increased for more "Human" chaos
                "top_p": 0.92
            }
        }
        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            return f"[Internal Error: {str(e)}]"
