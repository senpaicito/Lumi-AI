# Project LUMI (Local AI Companion)

**Disclaimer:** This entire project, including its architecture, logic, and documentation, was generated completely by an AI.

## Overview
Project LUMI is a highly advanced, locally hosted AI companion integrated with Discord. It is designed to emulate human-like memory, emotional processing, and autonomous behavior. The system architecture is heavily optimized for a multi-GPU environment (specifically tailored for an Intel i9-9940x, 64GB DDR4 RAM, and a dual-GPU setup featuring a Quadro RTX 4000 and Quadro T1000) to handle asynchronous background tasks without interrupting the primary conversational loop.

## Core Features

### 1. Multi-User & Server Awareness
LUMI independently tracks and manages interactions for multiple users simultaneously across DMs and servers. Each user receives an isolated memory profile. Long-term memories, emotional states, and relationship tracking are partitioned strictly by Discord ID to prevent cross-contamination of data.

### 2. Advanced Memory Architecture
*   **Short-Term Memory (STM):** Utilizes a 5-second asynchronous message buffer. This allows the AI to group rapid back-to-back messages (double-texting) into a single context window. It features interruption awareness, recognizing when a user sends a message while the AI is currently generating a response, and reacts accordingly.
*   **Long-Term Memory (LTM):** Powered by ChromaDB. Persistent memories are stored as vector embeddings and recalled dynamically via semantic search to inform future conversations.

### 3. Subconscious Emotional Engine
The AI does not rely on a static personality. It features a dynamic emotional state tracked individually per user, including metrics for Mood, Energy, Stress, and Intimacy.
*   **Emotional Decay:** Extreme emotional spikes gradually return to a baseline over time.
*   **Emotional Text Formatting:** The AI alters its syntax based on its current emotional state with a specific user. For example, it utilizes all caps during high energy states, or omits punctuation and capitalization entirely during high stress or low mood states.

### 4. Hardware-Accelerated Advanced Tasks
By leveraging a dual-GPU architecture, LUMI processes heavy secondary tasks asynchronously to preserve chat responsiveness:
*   **Dream Logs (REM Sleep):** During scheduled off-hours, the AI scans recent LTM interactions to generate private, highly introspective diary entries about specific users. These are stored locally and are accessible privately via command.
*   **YouTube Asynchronous Processing:** Users can send YouTube links to the AI. Using `yt-dlp` and `whisper`, the secondary GPU downloads and transcribes the video in the background. Once transcription is complete, the primary model reviews the content and pings the user with a customized critique.

### 5. Autonomy 2.0 (Proactive Engagement)
LUMI features an independent background heartbeat loop. If enabled by the user, the AI tracks the time elapsed since their last interaction. If the user has been inactive for a set duration (e.g., 4 hours), the AI will autonomously generate and send an organic check-in message directly to their DMs. This feature is strictly disabled in public server channels to respect boundaries.

## Command Reference
*   `/ping` - Checks if the bot is online and returns latency.
*   `/status` - Displays the AI's current emotional state (Mood, Energy, Stress) and Intimacy level specifically regarding the user invoking the command.
*   `/diary` - Retrieves and privately displays the most recent diary entry the AI has written about the user.
*   `/watch <url>` - Submits a YouTube link for the AI to download, transcribe, and review asynchronously.
*   `/engagement <True/False>` - Toggles whether the AI is allowed to proactively initiate conversations in the user's DMs.
*   `/reset` - Clears the user's specific short-term memory buffer in the current channel.
*   `/force` - Manually forces the subconscious engine to analyze the current interaction and update emotional states.
*   `/fullreset` - Completely wipes the user's personal profile, LTM vector collections, and emotional state data.
*   `/edit <path> <value>` - Developer command to manually modify variables within the core `character_card.json` on the fly.

## Dependencies
Ensure the following packages are installed via `pip install -r requirements.txt`:
*   `discord.py`
*   `chromadb`
*   `requests`
*   `yt-dlp`
*   `openai-whisper`



"creator" Here. this project was built on an i9-9940x system, with 64gb of ddr4, quadro rtx 4000, and a quadro t1000. There are alot of things running here. it is HIGHLY reccomended to dedicate a system to it.