import os
import shutil
from pathlib import Path
import asyncio
from typing import List, Union

# FIX: Dynamically determine BASE_DIR based on the new BASE_DIR from memory.py
# Assuming memory.py is imported and its BASE_DIR is the source of truth
import memory
BASE_DIR = memory.BASE_DIR

# --- CRITICAL CONFIGURATION FOR FILE ACCESS ---
# Define the BASE_FILE_ACCESS_DIR. All file operations by Francine
# will be restricted to paths *within* this directory.
#
# !!! WARNING !!!
# Setting this to your entire Desktop (e.g., Path.home() / "Desktop")
# is HIGHLY RISKY. A single LLM hallucination or misinterpretation of
# a "delete" or "move" command could lead to irreversible data loss.
#
# RECOMMENDATION: Start with a specific, isolated subfolder for Francine to manage.
# For example: BASE_DIR / "ManagedFiles"
#
BASE_FILE_ACCESS_DIR = BASE_DIR / "ManagedFiles" # FIX: Relative to new dynamic BASE_DIR
BASE_FILE_ACCESS_DIR.mkdir(parents=True, exist_ok=True) # Ensure this base directory exists

def _get_safe_path(requested_path: str) -> Path:
    """
    Ensures the requested path is within the BASE_FILE_ACCESS_DIR.
    Raises ValueError if the path attempts to go outside the allowed directory.
    """
    full_path = BASE_FILE_ACCESS_DIR / requested_path
    # Resolve the path to get its absolute, normalized form
    full_path = full_path.resolve()
    # Check if the resolved path is still a subpath of the base access directory
    # Path.is_relative_to requires Python 3.9+
    if not full_path.is_relative_to(BASE_FILE_ACCESS_DIR.resolve()):
        raise ValueError(f"Access denied: Path '{requested_path}' is outside the allowed directory.")
    return full_path

async def list_directory_contents(path: str = ".") -> List[str]:
    """
    Lists the contents (files and directories) of a specified path within the allowed access directory.
    Defaults to the base access directory if no path is provided.
    """
    try:
        safe_path = _get_safe_path(path)
        if not safe_path.is_dir():
            return [f"Error: '{path}' is not a directory or does not exist."]

        contents = []
        # os.listdir is synchronous, run in a thread
        for item in await asyncio.to_thread(os.listdir, safe_path):
            item_path = safe_path / item
            if item_path.is_file():
                contents.append(f"FILE: {item}")
            elif item_path.is_dir():
                contents.append(f"DIR: {item}")
        return contents
    except ValueError as e:
        return [f"Error: {e}"]
    except Exception as e:
        return [f"Error listing contents of '{path}': {e}"]

async def read_text_file(path: str) -> str:
    """
    Reads the text content of a specified file within the allowed access directory.
    """
    try:
        safe_path = _get_safe_path(path)
        if not safe_path.is_file():
            return f"Error: File '{path}' not found or is not a file."
        
        # Open file in a thread to prevent blocking
        content = await asyncio.to_thread(safe_path.read_text, encoding='utf-8')
        return content
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error reading file '{path}': {e}"

async def write_text_file(path: str, content: str, overwrite: bool = False) -> str:
    """
    Writes text content to a specified file within the allowed access directory.
    Can optionally overwrite existing files.
    """
    try:
        safe_path = _get_safe_path(path)
        if safe_path.exists() and not overwrite:
            return f"Error: File '{path}' already exists. Set overwrite=True to replace it."
        
        safe_path.parent.mkdir(parents=True, exist_ok=True) # Ensure parent directory exists
        
        # Write file in a thread to prevent blocking
        await asyncio.to_thread(safe_path.write_text, content, encoding='utf-8')
        return f"Successfully wrote content to '{path}'."
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error writing to file '{path}': {e}"

async def move_file(source_path: str, destination_path: str) -> str:
    """
    Moves a file from source_path to destination_path, both within the allowed access directory.
    """
    try:
        safe_source_path = _get_safe_path(source_path)
        safe_dest_path = _get_safe_path(destination_path)

        if not safe_source_path.exists():
            return f"Error: Source file/directory '{source_path}' does not exist."
        
        # Ensure destination's parent directory exists
        safe_dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Move file in a thread to prevent blocking
        await asyncio.to_thread(shutil.move, safe_source_path, safe_dest_path)
        return f"Successfully moved '{source_path}' to '{destination_path}'."
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error moving '{source_path}' to '{destination_path}': {e}"

async def delete_file(path: str) -> str:
    """
    Deletes a file or an empty directory within the allowed access directory.
    """
    try:
        safe_path = _get_safe_path(path)
        if not safe_path.exists():
            return f"Error: File/directory '{path}' does not exist."
        
        if safe_path.is_file():
            await asyncio.to_thread(os.remove, safe_path)
            return f"Successfully deleted file '{path}'."
        elif safe_path.is_dir():
            # Only delete empty directories for safety
            if not await asyncio.to_thread(os.listdir, safe_path):
                await asyncio.to_thread(os.rmdir, safe_path)
                return f"Successfully deleted empty directory '{path}'."
            else:
                return f"Error: Directory '{path}' is not empty. Cannot delete non-empty directories for safety."
        return f"Error: Cannot delete '{path}'. It's not a file or an empty directory."
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error deleting '{path}': {e}"

async def create_directory(path: str) -> str:
    """
    Creates a new directory (and any necessary parent directories) within the allowed access directory.
    """
    try:
        safe_path = _get_safe_path(path)
        # mkdir with parents=True creates intermediate directories
        # exist_ok=True prevents error if directory already exists
        await asyncio.to_thread(safe_path.mkdir, parents=True, exist_ok=True)
        return f"Successfully created directory '{path}'."
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error creating directory '{path}': {e}"
