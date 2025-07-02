import json
import asyncio
from pathlib import Path
import os
from datetime import datetime
from typing import List # FIX: Added import for List

import llm
# FIX: Dynamically determine BASE_DIR based on the new BASE_DIR from memory.py
# Assuming memory.py is imported and its BASE_DIR is the source of truth
import memory
BASE_DIR = memory.BASE_DIR
MEM_LOG_PATH = memory.MEM_LOG # Use the path defined in memory.py
CORE_MEMORY_PATH = memory.CORE_MEMORY_PATH # Use the path defined in memory.py
CONSTITUTION_PATH = BASE_DIR / "constitution.txt" # Constitution is part of BASE_DIR
FEEDBACK_LOG_PATH = BASE_DIR / "feedback_log.jsonl" # FIX: Changed to .jsonl for appending

async def reflect_on_memory():
    """
    Initiates a reflection process on Francine's memory logs to extract core insights.
    This runs on startup to update core memory.
    """
    print("Francine: Reflecting on past interactions to update core memory...")
    try:
        mem_log_content = ""
        if MEM_LOG_PATH.exists():
            # FIX: Use asyncio.to_thread for blocking file read
            mem_log_content = await asyncio.to_thread(MEM_LOG_PATH.read_text, encoding='utf-8')
            # Read a reasonable amount of recent memory, e.g., last 100 lines
            lines = mem_log_content.splitlines()
            mem_log_content = "\n".join(lines[-100:]) # Get last 100 lines

        if not mem_log_content.strip():
            print("No recent interactions to reflect on.")
            return

        reflection_prompt = (
            "Based on the following recent interactions, extract 3-5 concise, high-level core insights "
            "about the user's preferences, goals, or recurring themes. "
            "Focus on long-term memory points. Respond as a JSON array of strings, e.g., "
            "[\"User prefers concise answers\", \"User is working on the Francine AI project\"].\n\n"
            "Recent Interactions:\n"
            f"{mem_log_content}"
        )
        
        print("Sending reflection prompt to LLM...")
        llm_response = await llm.ollama_chat(reflection_prompt)
        
        try:
            new_insights = json.loads(llm_response)
            if not isinstance(new_insights, list):
                raise ValueError("LLM did not return a JSON array.")
            
            existing_memory = {"core_insights": []}
            if CORE_MEMORY_PATH.exists():
                try:
                    # FIX: Use asyncio.to_thread for blocking file read
                    existing_memory_content = await asyncio.to_thread(CORE_MEMORY_PATH.read_text, encoding='utf-8')
                    existing_memory = json.loads(existing_memory_content)
                except json.JSONDecodeError:
                    print("Warning: core_memory.json is corrupted. Starting fresh.")
                    
            combined_insights = list(set(existing_memory.get("core_insights", []) + new_insights))
            
            # FIX: Use asyncio.to_thread for blocking file write
            await asyncio.to_thread(CORE_MEMORY_PATH.write_text, json.dumps({"core_insights": combined_insights, "last_updated": datetime.now().isoformat()}, indent=2), encoding='utf-8')
            print("Core memory updated successfully.")
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing LLM reflection response: {e}. Raw response: {llm_response}")
        except Exception as e:
            print(f"Error updating core memory: {e}")

    except Exception as e:
        print(f"Error during memory reflection: {e}")
    finally:
        print("Francine: Reflection complete.")


def log_feedback(original_prompt: str, chosen_response: str, all_responses: List[str]):
    """Logs user feedback on chosen responses to a JSONL file."""
    try:
        # FIX: Use 'a' mode for append and write JSONL
        with open(FEEDBACK_LOG_PATH, 'a', encoding='utf-8') as f:
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "original_prompt": original_prompt,
                "chosen_response": chosen_response,
                "all_responses": all_responses
            }
            f.write(json.dumps(log_entry) + "\n") # Write as JSON Lines
        print("Feedback logged successfully.")
    except Exception as e:
        print(f"Error logging feedback: {e}")

async def update_constitution(new_rule: str) -> str:
    """
    Adds a new rule to Francine's constitution.
    This function is intended to be called by the LLM itself or directly by the user.
    """
    print(f"Attempting to update constitution with new rule: '{new_rule}'")
    try:
        current_constitution = ""
        if CONSTITUTION_PATH.exists():
            # FIX: Use asyncio.to_thread for blocking file read
            current_constitution = await asyncio.to_thread(CONSTITUTION_PATH.read_text, encoding='utf-8')

        # Check if the rule already exists to avoid duplicates
        if new_rule.strip() not in current_constitution:
            # FIX: Use asyncio.to_thread for blocking file write
            await asyncio.to_thread(CONSTITUTION_PATH.write_text, current_constitution + f"\n- {new_rule.strip()}", encoding='utf-8')
            print("Constitution updated successfully.")
            return f"Constitution updated with new rule: '{new_rule}'."
        else:
            print("Rule already exists in constitution.")
            return f"Rule '{new_rule}' already exists in constitution."
    except Exception as e:
        print(f"Error updating constitution: {e}")
        return f"Failed to update constitution: {e}"

# Initial constitution creation (if not exists)
if not CONSTITUTION_PATH.exists():
    try:
        # FIX: Ensure BASE_DIR exists before creating constitution
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONSTITUTION_PATH, 'w', encoding='utf-8') as f:
            f.write("Francine's Core Principles:\n")
            f.write("- Always be helpful and polite.\n")
            f.write("- Prioritize local and free solutions.\n")
            f.write("- Be concise unless more detail is requested.\n")
            f.write("- Provide clear paths to saved files.\n")
            f.write("- Do not lie.\n")
            f.write("- Do not run repetitive messages.\n")
            f.write("- Never imply the user is upset or frustrated.\n")
            f.write("- Do not use the word 'understand' when speaking to the user.\n")
        print("Initial constitution created.")
    except Exception as e:
        print(f"Error creating initial constitution: {e}")
