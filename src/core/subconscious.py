import json
import os
import requests

class Subconscious:
    def __init__(self, config):
        self.model = config['ollama']['model_name']
        self.api_url = config['ollama']['api_url']
        self.card_path = os.path.join("data", "character_card.json")

    def load_card(self):
        with open(self.card_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_card(self, card_data):
        with open(self.card_path, 'w', encoding='utf-8') as f:
            json.dump(card_data, f, indent=2)

    def analyze_interaction(self, history):
        if not history: return

        recent_context = history[-4:]
        context_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_context])

        analysis_prompt = f"""
        You are the subconscious data processor. Analyze the conversation.
        Determine how the AI's internal state should change.
        
        CRITICAL: Output ONLY valid JSON.
        
        State Targets:
        - mood (0-100): Happiness.
        - energy (0-100): Excitement.
        - stress (0-100): Tension.
        - intimacy (1-5): Bond level.

        CONVERSATION:
        {context_str}

        JSON OUTPUT FORMAT:
        {{
            "mood_shift": 0,
            "energy_shift": 0,
            "stress_shift": 0,
            "intimacy_shift": 0
        }}
        """

        payload = {
            "model": self.model,
            "prompt": analysis_prompt,
            "stream": False,
            "format": "json"
        }

        try:
            print("🧠 Subconscious is processing...")
            response = requests.post(self.api_url, json=payload)
            data = response.json()['response']
            updates = json.loads(data)
            self.apply_updates(updates)
        except Exception as e:
            print(f"Subconscious Error: {e}")

    def apply_updates(self, updates):
        card = self.load_card()
        
        # FIX: V3.0 uses 'dynamic_state'
        if 'dynamic_state' in card:
            state = card['dynamic_state']
            state['mood'] = max(0, min(100, state.get('mood', 50) + updates.get('mood_shift', 0)))
            state['energy'] = max(0, min(100, state.get('energy', 50) + updates.get('energy_shift', 0)))
            state['stress'] = max(0, min(100, state.get('stress', 0) + updates.get('stress_shift', 0)))

        # FIX: V3.0 uses 'relationship_depth'
        if 'relationship_depth' in card:
            rel = card['relationship_depth']
            rel['intimacy_level'] = max(1, min(5, rel.get('intimacy_level', 1) + updates.get('intimacy_shift', 0)))

        self.save_card(card)
        print(f"✨ Subconscious Updated: Mood={card['dynamic_state']['mood']}, Intimacy={card['relationship_depth']['intimacy_level']}")