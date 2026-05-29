import asyncio
import os
import yt_dlp
import whisper

class AdvancedTasks:
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

    async def process_rem_sleep(self):
        print("💤 Triggering REM Sleep & Diary Generation...")
        memory_dir = self.bot.memory_manager.memory_dir
        for filename in os.listdir(memory_dir):
            if filename.endswith(".json") and filename != "diary":
                user_id = filename.replace(".json", "")
                profile = self.bot.memory_manager.get_user_profile(user_id)
                alias = profile.get("associated_name", "Stranger")
                
                recent_memories = self.bot.memory_manager.get_recent_ltm(user_id, limit=15)
                if recent_memories:
                    mem_str = "\n".join(recent_memories)
                    prompt = f"Write a deeply personal, introspective, indie-goth diary entry about your relationship with {alias} based on today's memories:\n{mem_str}\nDo not use robotic formatting, make it look like a real diary."
                    
                    diary_entry = await asyncio.to_thread(self.bot.ollama._send_request, prompt)
                    self.bot.memory_manager.save_diary_entry(user_id, diary_entry)
                    print(f"📖 Wrote a diary entry for {alias}!")

    def extract_youtube_transcript(self, url):
        # yt-dlp configuration to extract audio
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'temp_audio_%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_file = f"temp_audio_{info['id']}.mp3"
            
        # Whisper transcription
        model = whisper.load_model("base")
        result = model.transcribe(audio_file)
        
        # Cleanup
        if os.path.exists(audio_file):
            os.remove(audio_file)
            
        return result["text"]

    async def process_youtube_video(self, url, user_id, channel):
        try:
            print(f"📺 Downloading and transcribing {url}...")
            
            # Run the heavy extraction and transcription on a separate thread
            transcript = await asyncio.to_thread(self.extract_youtube_transcript, url)
            
            # Truncate if the video is excessively long to save token space
            if len(transcript) > 3000:
                transcript = transcript[:3000] + "... [Video continues]"
            
            profile = self.bot.memory_manager.get_user_profile(user_id)
            alias = profile.get("associated_name", "Stranger")
            
            prompt = f"[SYSTEM: {alias} sent you a YouTube video. The transcript is: '{transcript}'. Write a cynical, unfiltered, indie-goth critique of this video and tag {alias}.]"
            
            review = await asyncio.to_thread(self.bot.ollama._send_request, prompt)
            formatted = self.bot.apply_emotional_formatting(review, user_id)
            await channel.send(f"<@{user_id}> {formatted}")
            
        except Exception as e:
            print(f"YouTube Processing Error: {e}")
            await channel.send(f"<@{user_id}> Ugh, the link broke or the video was too weird. Nevermind.")
