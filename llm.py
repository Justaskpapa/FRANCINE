import httpx # Changed from 'requests' for async operations
import json
import os

# OLLAMA_HOST environment variable ensures flexibility, default to localhost
OLLAMA = os.getenv("OLLAMA_HOST", "http://localhost:11434")

async def ollama_chat(prompt: str, model: str = "gemma3:12b-it-q4_K_M") -> str:
    """
    Sends a prompt to the Ollama chat model asynchronously and returns the response.
    Uses httpx for non-blocking network requests.
    """
    async with httpx.AsyncClient() as client: # Use AsyncClient for async requests
        try:
            r = await client.post( # Use await for async operations
                f"{OLLAMA}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=60.0 # Add a timeout for robustness
            )
            r.raise_for_status()  # Raise an HTTPStatusError for bad responses (4xx or 5xx)
            return r.json()["response"]
        except httpx.RequestError as e: # Catch httpx specific exceptions
            print(f"Error communicating with Ollama chat API: {e}")
            return f"Error: Could not get a response from the LLM. {e}"
        except json.JSONDecodeError:
            print("Error: Ollama response was not valid JSON.")
            return "Error: Invalid response from LLM."

async def ollama_embed(text: str, model: str = "minilm:latest") -> list[float]:
    """
    Sends text to the Ollama embedding model asynchronously and returns the embedding vector.
    Uses httpx for non-blocking network requests.
    """
    async with httpx.AsyncClient() as client: # Use AsyncClient for async requests
        try:
            r = await client.post( # Use await for async operations
                f"{OLLAMA}/api/embeddings",
                json={"model": model, "prompt": text},
                timeout=60.0 # Add a timeout for robustness
            )
            r.raise_for_status()  # Raise an HTTPStatusError for bad responses (4xx or 5xx)
            return r.json()["embedding"]
        except httpx.RequestError as e: # Catch httpx specific exceptions
            print(f"Error communicating with Ollama embeddings API: {e}")
            return []  # Return empty list on failure
        except json.JSONDecodeError:
            print("Error: Ollama embedding response was not valid JSON.")
            return []
