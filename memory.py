import json
import os
from pathlib import Path

# Base directory for persistent storage
# FIX: Dynamically determine BASE_DIR based on user's home directory for portability
# This will create a 'FrancineData' folder inside the user's home directory.
BASE_DIR = Path.home() / "FrancineData"
BASE_DIR.mkdir(parents=True, exist_ok=True) # Ensure this base directory exists

PROFILE_PATH = BASE_DIR / "user_profile.json"
MEM_LOG = BASE_DIR / "memlog.txt"
CORE_MEMORY_PATH = BASE_DIR / "core_memory.json" # Added core memory path

def load_user_profile() -> dict:
    """Loads the user profile from disk."""
    if PROFILE_PATH.exists():
        try:
            with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Warning: user_profile.json is corrupted. Returning empty profile.")
            return {}
    return {}

def save_user_profile(data: dict) -> None:
    """Saves the user profile to disk."""
    # BASE_DIR.mkdir(parents=True, exist_ok=True) # Already ensured at module level
    try:
        with open(PROFILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        from debug import auto_fix
        auto_fix(e)

def log_interaction(prompt: str, response: str) -> None:
    """Logs each interaction for RAG and memory purposes."""
    # BASE_DIR.mkdir(parents=True, exist_ok=True) # Already ensured at module level
    try:
        with open(MEM_LOG, 'a', encoding='utf-8') as f:
            f.write(f"USER: {prompt}\nAI: {response}\n\n")
    except Exception as e:
        from debug import auto_fix
        auto_fix(e)
