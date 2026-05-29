import json
import os
import requests
import traceback

class Subconscious:
    def __init__(self, config):
        self.config = config
        self.model = config['ollama']['model_name']
        self.api_url = config['ollama']['api_url']

    def analyze_interaction(self, channel_short_term_memory, user_id, user_alias):
        if not channel_short_term_memory: return

        recent_context = channel_short_term_memory[-5:]
        context_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_context])

        analysis_prompt = f"""
        You are the subconscious data processor. Analyze the following group conversation.
        Determine how the AI's internal state should change based SPECIFICALLY on the interaction with {user_alias}.
        Also, check if {user_alias} explicitly stated their name or what they want to be called.
        
        CRITICAL: Output ONLY valid JSON.
        
        State Targets:
        - mood_shift (-10 to 10): Change in Happiness based on interaction with {user_alias}.
        - energy_shift (-10 to 10): Change in Excitement.
        - stress_shift (-10 to 10): Change in Tension.
        - intimacy_shift (0.0 to 1.0): Bond growth with {user_alias}.
        - user_name_update (String or null): ONLY provide a name if {user_alias} clearly stated it in this specific conversation. Otherwise, output null.

        CONVERSATION:
        {context_str}

        JSON OUTPUT FORMAT:
        {{
            "mood_shift": 0,
            "energy_shift": 0,
            "stress_shift": 0,
            "intimacy_shift": 0,
            "user_name_update": null
        }}
        """

        payload = {
            "model": self.model,
            "prompt": analysis_prompt,
            "stream": False,
            "format": "json"
        }

        try:
            print(f"🧠 [DEBUG] Subconscious is processing interaction with {user_alias}...")
            response = requests.post(self.api_url, json=payload)
            data = response.json()['response']
            updates = json.loads(data)
            self.apply_updates(updates, user_id)
        except Exception as e:
            print(f"🚨 [CRITICAL ERROR] Subconscious Error: {e}")
            traceback.print_exc()

    def apply_updates(self, updates, user_id):
        try:
            user_file = os.path.join("data", "memory", f"{user_id}.json")
            if os.path.exists(user_file):
                with open(user_file, 'r', encoding='utf-8') as uf:
                    user_profile = json.load(uf)
            else:
                user_profile = {
                    "author_id": str(user_id), 
                    "associated_name": "Stranger", 
                    "intimacy_level": 1, 
                    "shared_lore": [], 
                    "last_interaction": "",
                    "dynamic_state": {
                        "mood": 50, "mood_baseline": 50,
                        "energy": 50, "energy_baseline": 50,
                        "stress": 0, "stress_baseline": 0,
                        "decay_rate": 2.0
                    }
                }

            state = user_profile.setdefault('dynamic_state', {
                "mood": 50, "mood_baseline": 50,
                "energy": 50, "energy_baseline": 50,
                "stress": 0, "stress_baseline": 0,
                "decay_rate": 2.0
            })
            
            mood_base = state.get('mood_baseline', 50)
            energy_base = state.get('energy_baseline', 50)
            stress_base = state.get('stress_baseline', 0)
            decay = state.get('decay_rate', 2.0)
            
            if state['mood'] > mood_base: state['mood'] = max(mood_base, state['mood'] - decay)
            elif state['mood'] < mood_base: state['mood'] = min(mood_base, state['mood'] + decay)
            
            if state['energy'] > energy_base: state['energy'] = max(energy_base, state['energy'] - decay)
            elif state['energy'] < energy_base: state['energy'] = min(energy_base, state['energy'] + decay)
            
            if state['stress'] > stress_base: state['stress'] = max(stress_base, state['stress'] - decay)
            elif state['stress'] < stress_base: state['stress'] = min(stress_base, state['stress'] + decay)
            
            state['mood'] = max(0, min(100, state['mood'] + updates.get('mood_shift', 0)))
            state['energy'] = max(0, min(100, state['energy'] + updates.get('energy_shift', 0)))
            state['stress'] = max(0, min(100, state['stress'] + updates.get('stress_shift', 0)))

            user_profile['intimacy_level'] = min(10, user_profile.get('intimacy_level', 1) + updates.get('intimacy_shift', 0))

            new_name = updates.get('user_name_update')
            if new_name and isinstance(new_name, str) and new_name.lower() != 'null':
                user_profile['associated_name'] = new_name
                print(f"✨ [DEBUG] Subconscious learned a new name: {new_name}!")

            with open(user_file, 'w', encoding='utf-8') as uf:
                json.dump(user_profile, uf, indent=2)
                
            print(f"✨ [DEBUG] Subconscious Updated for {user_profile.get('associated_name')}: Mood={state['mood']}, Intimacy={user_profile['intimacy_level']}")
        except Exception as e:
            print(f"🚨 [CRITICAL ERROR] Failed to apply subconscious updates: {e}")
            traceback.print_exc()
