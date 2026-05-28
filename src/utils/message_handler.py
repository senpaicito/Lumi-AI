import asyncio

async def send_split_message(destination, text):
    """
    Splits text into chunks of 1900 chars (safety buffer for Discord's 2000 limit)
    while avoiding breaking words or sentences awkwardly.
    """
    if not text:
        return

    limit = 1900
    
    if len(text) <= limit:
        await destination.send(text)
        return

    chunks = []
    while len(text) > limit:
        # Find the nearest sentence end (. ! ?) before the limit
        split_index = -1
        for punct in ['.', '!', '?', '\n']:
            idx = text.rfind(punct, 0, limit)
            if idx > split_index:
                split_index = idx
        
        # If no sentence end found, try nearest space
        if split_index == -1:
            split_index = text.rfind(" ", 0, limit)
        
        # If no space found (huge block of text), hard cut
        if split_index == -1:
            split_index = limit
        else:
            split_index += 1 # Include the punctuation/space
            
        chunks.append(text[:split_index])
        text = text[split_index:]
    
    chunks.append(text) # Add remainder

    for chunk in chunks:
        if chunk.strip():
            await destination.send(chunk)
            await asyncio.sleep(1) # Pace the messages