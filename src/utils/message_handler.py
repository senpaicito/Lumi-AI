import asyncio
import traceback

async def send_split_message(destination, text, reply_to=None):
    """
    Splits text into chunks of 1900 chars (safety buffer for Discord's 2000 limit)
    while avoiding breaking words or sentences awkwardly.
    Now supports direct inline replies!
    """
    if not text:
        return

    limit = 1900
    
    try:
        if len(text) <= limit:
            if reply_to:
                await reply_to.reply(text)
            else:
                await destination.send(text)
            return

        chunks = []
        while len(text) > limit:
            split_index = -1
            for punct in ['.', '!', '?', '\n']:
                idx = text.rfind(punct, 0, limit)
                if idx > split_index:
                    split_index = idx
            
            if split_index == -1:
                split_index = text.rfind(" ", 0, limit)
            
            if split_index == -1:
                split_index = limit
            else:
                split_index += 1 
                
            chunks.append(text[:split_index])
            text = text[split_index:]
        
        chunks.append(text) 

        for i, chunk in enumerate(chunks):
            if chunk.strip():
                if i == 0 and reply_to:
                    await reply_to.reply(chunk)
                else:
                    await destination.send(chunk)
                await asyncio.sleep(1) 
    except Exception as e:
        print(f"🚨 [CRITICAL ERROR] Failed to send split message: {e}")
        traceback.print_exc()
