import json
import os
import typer
from pathlib import Path
from typing import Callable, Awaitable, Dict, Union, List, Any
import asyncio
import re
import threading # For running the scheduler in a background thread

# Import your existing modules directly, assuming they are in the same directory as main.py
import llm
import voice
import memory
from memory import log_interaction # Specific import from memory
import osint
import ecommerce
import docs
import rag
import scheduler # Now contains run_scheduler_in_background
import web_scrape
import file_manager
import browser # Import browser for cleanup_browser
import debug # For auto_fix

# --- NEW: Import the evolution module ---
import evolution # For reflection and constitution updates

app = typer.Typer()

# --- NEW: TOOL_SCHEMA for LLM to understand function parameters ---
# This provides the LLM with the exact structure of each tool's arguments.
TOOL_SCHEMA = [
    {"name": "recon_username", "description": "Performs OSINT on a given username across various platforms.", "parameters": {"type": "object", "properties": {"u": {"type": "string", "description": "The username to perform OSINT on."}}, "required": ["u"]}},
    {"name": "recon_email", "description": "Performs OSINT on a given email address.", "parameters": {"type": "object", "properties": {"e": {"type": "string", "description": "The email address to perform OSINT on."}}, "required": ["e"]}},
    {"name": "recon_person", "description": "Performs OSINT on a person given their name and location.", "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "The person's full name."}, "loc": {"type": "string", "description": "The person's location."}}, "required": ["name", "loc"]}},
    {"name": "recon_vehicle", "description": "Performs OSINT on a vehicle given its VIN.", "parameters": {"type": "object", "properties": {"vin": {"type": "string", "description": "The Vehicle Identification Number (VIN)."}}, "required": ["vin"]}},
    {"name": "recon_domain", "description": "Performs OSINT on a domain, including WHOIS and DNS records.", "parameters": {"type": "object", "properties": {"dom": {"type": "string", "description": "The domain name."}}, "required": ["dom"]}},
    {"name": "recon_ip", "description": "Performs OSINT on an IP address.", "parameters": {"type": "object", "properties": {"ip": {"type": "string", "description": "The IP address."}}, "required": ["ip"]}},
    {"name": "spiderfoot_scan", "description": "Initiates a SpiderFoot scan and returns the path to the JSON report. (Placeholder)", "parameters": {"type": "object", "properties": {"target": {"type": "string", "description": "The target for the SpiderFoot scan (e.g., domain, IP, username)."}}, "required": ["target"]}},
    {"name": "product_research_ali", "description": "Searches AliExpress for products based on keywords and returns a list of product details.", "parameters": {"type": "object", "properties": {"kw": {"type": "string", "description": "Keywords for product search."}}, "required": ["kw"]}},
    {"name": "tiktok_trend_scrape", "description": "Scrapes TikTok for trending videos/data related to a given hashtag.", "parameters": {"type": "object", "properties": {"tag": {"type": "string", "description": "The hashtag to scrape TikTok trends for."}}, "required": ["tag"]}},
    {"name": "profit_calc", "description": "Calculates potential profit given revenue, cost of goods sold, shipping, and advertising costs.", "parameters": {"type": "object", "properties": {"revenue": {"type": "number", "description": "Total revenue from sales."}, "cogs": {"type": "number", "description": "Cost of Goods Sold."}, "ship": {"type": "number", "description": "Shipping cost."}, "ads": {"type": "number", "description": "Advertising cost."}}, "required": ["revenue", "cogs", "ship", "ads"]}},
    {"name": "shopify_api_upload", "description": "Uploads product data to Shopify via API and returns the product ID. (Placeholder)", "parameters": {"type": "object", "properties": {"prod_json": {"type": "object", "description": "JSON object representing product data."}}, "required": ["prod_json"]}},
    {"name": "pdf_read", "description": "Reads text content from a PDF file.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "The path to the PDF file."}}, "required": ["path"]}},
    {"name": "pdf_autofill", "description": "Autofills specified fields in a PDF form and returns the path to the new PDF.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "The path to the PDF form file."}, "field_dict": {"type": "object", "description": "A dictionary of form field names and their values."}}, "required": ["path", "field_dict"]}},
    {"name": "pdf_generate", "description": "Generates a PDF from Markdown text and returns the path to the new PDF.", "parameters": {"type": "object", "properties": {"markdown_text": {"type": "string", "description": "The Markdown formatted text to convert to PDF."}}, "required": ["markdown_text"]}},
    {"name": "rag_query", "description": "Queries the FAISS index for relevant documents and returns a list of (text, score) tuples.", "parameters": {"type": "object", "properties": {"question": {"type": "string", "description": "The question to query the RAG index with."}, "k": {"type": "integer", "description": "The number of top results to retrieve (default 3)."}}, "required": ["question"]}},
    {"name": "schedule_job", "description": "Schedules a job to run at specified intervals using a cron-like expression. (Non-blocking)", "parameters": {"type": "object", "properties": {"cron_expression": {"type": "string", "description": "A cron-like expression (e.g., 'HH:MM' for daily)."}, "command": {"type": "string", "description": "The shell command to execute."}}, "required": ["cron_expression", "command"]}},
    {"name": "scrape_text_content", "description": "Navigates to a URL and returns its full text content for general web scraping.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "The URL to scrape."}, "selector": {"type": "string", "description": "CSS selector for the content to scrape (default 'body')."}}, "required": ["url"]}},
    {"name": "update_constitution", "description": "Adds a new rule to Francine's constitution.", "parameters": {"type": "object", "properties": {"new_rule": {"type": "string", "description": "The new rule to add to the constitution."}}, "required": ["new_rule"]}},
    {"name": "list_directory_contents", "description": "Lists contents of a directory within Francine's managed files.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "The path to the directory (relative to Francine_Managed_Files)."}}, "required": []}},
    {"name": "read_text_file", "description": "Reads text content of a file within Francine's managed files.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "The path to the file (relative to Francine_Managed_Files)."}}, "required": ["path"]}},
    {"name": "write_text_file", "description": "Writes text content to a file within Francine's managed files.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "The path to the file (relative to Francine_Managed_Files)."}, "content": {"type": "string", "description": "The text content to write."}, "overwrite": {"type": "boolean", "description": "Whether to overwrite if file exists (default false)."}}, "required": ["path", "content"]}},
    {"name": "move_file", "description": "Moves a file within Francine's managed files.", "parameters": {"type": "object", "properties": {"source_path": {"type": "string", "description": "The current path of the file."}, "destination_path": {"type": "string", "description": "The new path for the file."}}, "required": ["source_path", "destination_path"]}},
    {"name": "delete_file", "description": "Deletes a file or empty directory within Francine's managed files.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "The path to the file or empty directory."}}, "required": ["path"]}},
    {"name": "create_directory", "description": "Creates a new directory within Francine's managed files.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "The path of the new directory."}}, "required": ["path"]}},
]


# FUNCTION_MAP now maps to async functions where applicable
# FIX: Corrected type annotation for FUNCTION_MAP
FUNCTION_MAP: dict[str, Callable[..., Any]] = {
    "recon_username": osint.recon_username,
    "recon_email": osint.recon_email,
    "recon_person": osint.recon_person,
    "recon_vehicle": osint.recon_vehicle,
    "recon_domain": osint.recon_domain,
    "recon_ip": osint.recon_ip,
    "spiderfoot_scan": osint.spiderfoot_scan,
    "product_research_ali": ecommerce.product_research_ali,
    "tiktok_trend_scrape": ecommerce.tiktok_trend_scrape,
    "profit_calc": ecommerce.profit_calc,
    "shopify_api_upload": ecommerce.shopify_api_upload,
    "pdf_read": docs.pdf_read,
    "pdf_autofill": docs.pdf_autofill,
    "pdf_generate": docs.pdf_generate,
    "rag_query": rag.rag_query,
    "schedule_job": scheduler.schedule_job,
    "scrape_text_content": web_scrape.scrape_text_content,
    "update_constitution": evolution.update_constitution,
    "list_directory_contents": file_manager.list_directory_contents,
    "read_text_file": file_manager.read_text_file,
    "write_text_file": file_manager.write_text_file,
    "move_file": file_file_manager.move_file, # FIX: Corrected typo
    "delete_file": file_manager.delete_file,
    "create_directory": file_manager.create_directory,
}

# FIX: Dynamically determine BASE_DIR based on the new BASE_DIR from memory.py
# Assuming memory.py is imported and its BASE_DIR is the source of truth
import memory
BASE_DIR = memory.BASE_DIR

CONFIG_PATH = Path("./config.json") 


# --- NEW: Helper to speak responses ---
async def voice_speak(text: str):
    """Speaks text if voice mode is enabled."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r') as f:
                cfg = json.load(f)
                if cfg.get("speech", False):
                    await asyncio.to_thread(voice.tts_speak, text)
        except json.JSONDecodeError:
            pass 

# --- NEW: Human-in-the-Loop Clarification Function ---
async def ask_user_for_clarification(question: str) -> str:
    """
    Asks the user a clarifying question and returns their response.
    This function is called internally by the agent's logic.
    """
    print(f"Francine needs clarification: {question}")
    await voice_speak(f"I need clarification: {question}")
    clarification_response = typer.prompt("Your clarification")
    log_interaction("Francine (Clarification)", clarification_response)
    return clarification_response

# --- NEW: Tool Failure Reflection Function ---
async def reflect_on_tool_failure(tool_name: str, args_used: Dict, error_message: str, current_plan: str, context: str) -> Dict[str, Any]:
    """
    Uses the LLM to reflect on a tool failure and suggest a new approach or a clarifying question.
    Returns a new instruction for the LLM.
    """
    print(f"Francine: Reflecting on failure of '{tool_name}'...")
    
    # This TOOL_SCHEMA is defined globally at the top of the file.
    # It's included here to ensure the LLM has access to the schema for reflection.
    reflection_prompt = (
        "You attempted to use a tool, but it failed. Analyze the failure and suggest a new approach. "
        "Your response should be a JSON object with either:\n"
        "1. {\"action\": \"retry_with_new_args\", \"function\": \"<tool_name>\", \"args\": {...}, \"reason\": \"<why_this_new_attempt>\"}\n"
        "2. {\"action\": \"ask_user\", \"question\": \"<clarifying_question_for_user>\", "
        "\"reason\": \"<why_asking>\"}\n" # FIX: Added missing quote
        "3. {\"action\": \"give_up\", \"answer\": \"<explanation_to_user>\", \"reason\": \"<why_giving_up>\"}\n\n"
        "If suggesting a retry, ensure the 'function' and 'args' are valid for the tool. Use the TOOL_SCHEMA below for reference.\n\n"
        f"Tool Name: {tool_name}\n"
        f"Arguments Used: {json.dumps(args_used)}\n"
        f"Error Message: {error_message}\n"
        f"Current Plan/Goal: {current_plan}\n"
        f"Relevant Context: {context}\n\n"
        f"--- TOOL_SCHEMA ---\n{json.dumps(TOOL_SCHEMA, indent=2)}\n--- END TOOL_SCHEMA ---\n"
        "Suggest a new action:"
    )
    reflection_response_str = await llm.ollama_chat(reflection_prompt)
    try:
        reflection_response = json.loads(reflection_response_str)
        if not isinstance(reflection_response, dict) or "action" not in reflection_response:
            raise ValueError("Invalid reflection response format.")
        return reflection_response
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing LLM reflection response: {e}. Raw response: {reflection_response_str}")
        return {"action": "give_up", "answer": f"I encountered an unrecoverable error trying to use the tool '{tool_name}'. Error: {error_message}", "reason": "LLM failed to provide a valid reflection plan."}


# --- MODIFIED: The core prompt handler now incorporates advanced agent logic ---
async def handle_prompt(prompt: str, max_retries: int = 2):
    """
    Handles a user prompt with advanced agent capabilities:
    - Dynamic context retrieval.
    - Tool use with self-correction loops.
    - Human-in-the-loop clarification.
    - Advanced error handling.
    """
    current_prompt_for_llm = prompt # This prompt gets modified for retries/clarifications
    current_plan = "Initial user request." # Track the current goal/plan
    
    for retry_count in range(max_retries + 1): # Allow initial attempt + max_retries
        try:
            # --- Dynamically retrieve relevant context using RAG ---
            relevant_context = await rag.get_relevant_context(current_prompt_for_llm)
            
            # --- Minimalist LLM Instruction ---
            # Now includes the TOOL_SCHEMA for reliable function calling
            instruction = (
                "You are Francine, a helpful local AI assistant. Your primary goal is to fulfill user requests by calling internal functions. "
                "Respond with JSON like {\"function\":<name>, \"args\":{...}} or {\"function\":\"none\", \"answer\":\"<your_answer>\"}. "
                "Use the TOOL_SCHEMA below to understand available functions and their parameters.\n\n"
                f"--- TOOL_SCHEMA ---\n{json.dumps(TOOL_SCHEMA, indent=2)}\n--- END TOOL_SCHEMA ---\n"
            )
            
            if relevant_context:
                instruction += f"\n\n{relevant_context}"

            final_llm_prompt = f"{instruction}\nUser: {current_prompt_for_llm}"
            
            analysis = await llm.ollama_chat(final_llm_prompt)
            try:
                parsed = json.loads(analysis)
            except json.JSONDecodeError:
                # If LLM doesn't return valid JSON, treat it as a direct answer
                parsed = {"function": "none", "answer": analysis}

            func_name = parsed.get("function", "none")
            
            if func_name and func_name in FUNCTION_MAP:
                func = FUNCTION_MAP[func_name]
                args = parsed.get("args", {})
                
                tool_execution_successful = False
                tool_error_message = ""
                tool_result_data: Any = None # Raw data returned by the tool

                try:
                    # Execute the tool based on its type (async vs. sync)
                    # All functions are now either async or explicitly run in to_thread
                    if func_name == "profit_calc": # sync, fast, no to_thread needed
                        tool_result_data = func(**args)
                    elif func_name == "schedule_job": # sync, blocking, needs to_thread
                        print("Warning: schedule_job is a blocking function and should be run in a separate process/thread.")
                        tool_result_data = await asyncio.to_thread(func, **args)
                    elif func_name in [ # These are sync, blocking, needs to_thread
                        "recon_username", "recon_email", "recon_person", "recon_vehicle",
                        "recon_domain", "recon_ip", "spiderfoot_scan",
                        "product_research_ali", "tiktok_trend_scrape",
                        "pdf_read", "pdf_autofill", "pdf_generate",
                        "update_constitution" # evolution function is sync
                    ]:
                        tool_result_data = await asyncio.to_thread(func, **args)
                    else: # All other functions in FUNCTION_MAP are now async
                        tool_result_data = await func(**args)

                    tool_execution_successful = True # If we reach here, tool executed without Python error

                except Exception as tool_e:
                    tool_error_message = str(tool_e)
                    print(f"Francine: Tool '{func_name}' execution failed: {tool_error_message}")
                    auto_fix(tool_e) # Log the specific tool error

                # --- Process Tool Result / Handle Failure ---
                final_response_text = "" # What Francine will say/log
                if tool_execution_successful:
                    # --- NEW: Enhanced result processing based on tool type ---
                    if func_name in ["recon_username", "recon_email", "recon_person", "recon_vehicle", "recon_domain", "recon_ip", "spiderfoot_scan", "product_research_ali", "tiktok_trend_scrape"]:
                        if tool_result_data:
                            dump_path = osint._dump_result(func_name, tool_result_data)
                            final_response_text = f"Operation completed. Results saved to: {dump_path}"
                        else:
                            final_response_text = f"Operation completed, but no results were returned by {func_name}."
                    elif func_name == "scrape_text_content":
                        url = args.get('url', 'unknown_url')
                        if tool_result_data:
                            clean_url_prefix = url.replace('https://', '').replace('http://', '').split('/')[0].replace('.', '_').replace(':', '_')
                            prefix = f"web_scrape_{clean_url_prefix}"
                            dump_path = osint._save_result_to_file(prefix, tool_result_data, extension=".txt")
                            final_response_text = f"Web scrape completed. Text content saved to: {dump_path}. Snippet: {tool_result_data[:200]}..."
                        else:
                            result = f"Web scrape completed for {url}, but no content was returned."
                    elif func_name in ["pdf_read", "pdf_autofill", "pdf_generate"]:
                        if func_name == "pdf_read" and isinstance(tool_result_data, str):
                            prefix = f"pdf_content_{Path(args.get('path', 'unknown')).stem}"
                            dump_path = osint._save_result_to_file(prefix, tool_result_data, extension=".txt")
                            final_response_text = f"PDF content read and saved to: {dump_path}. Snippet: {tool_result_data[:200]}..."
                        elif isinstance(tool_result_data, str) and (tool_result_data.endswith(".pdf") or "generated.pdf" in tool_result_data):
                            final_response_text = f"Document operation completed. Output file: {tool_result_data}"
                        else:
                            final_response_text = f"Document operation completed, but result was unexpected: {tool_result_data}"
                    elif func_name == "rag_query":
                        if tool_result_data:
                            final_response_text = f"RAG query results: {tool_result_data}"
                        else:
                            final_response_text = "RAG query completed, but no relevant documents found."
                    elif func_name == "profit_calc":
                        final_response_text = f"The calculated value is: {tool_result_data}"
                    elif func_name == "update_constitution":
                        final_response_text = str(tool_result_data) # Already a string message
                    elif func_name in ["list_directory_contents", "read_text_file", "write_text_file", "move_file", "delete_file", "create_directory"]:
                        final_response_text = str(tool_result_data) # Already a string message
                    else:
                        final_response_text = f"Function {func_name} executed. Result: {tool_result_data}"
                    
                    # Tool executed successfully, so we are done with this prompt
                    log_interaction(prompt, final_response_text)
                    await voice_speak(final_response_text)
                    return # Exit handle_prompt after successful tool execution

                else: # Tool execution failed (tool_execution_successful is False)
                    print(f"Francine: Attempting to self-correct for '{func_name}' failure (Retry {retry_count+1}/{max_retries})...")
                    reflection_action = await reflect_on_tool_failure(
                        func_name, args, tool_error_message, current_plan, relevant_context
                    )

                    if reflection_action["action"] == "retry_with_new_args":
                        print(f"Francine: Retrying with new arguments: {reflection_action['args']}")
                        current_prompt_for_llm = f"User originally asked: '{prompt}'. Previous attempt to use '{func_name}' with args {args} failed: '{tool_error_message}'. Reason for retry: {reflection_action.get('reason', 'LLM suggested retry')}. Now try again based on this. Original prompt for LLM was: '{final_llm_prompt}'" # FIX: Simplified prompt
                        # Loop will continue to the next retry_count
                    elif reflection_action["action"] == "ask_user":
                        clarification = await ask_user_for_clarification(reflection_action["question"])
                        current_prompt_for_llm = f"User originally asked: '{prompt}'. My previous attempt failed. User clarified: '{clarification}'. Reason for asking: {reflection_action.get('reason', 'LLM needed clarification')}. Now try again based on this clarification. Original prompt for LLM was: '{final_llm_prompt}'" # FIX: Simplified prompt
                        # Loop will continue to the next retry_count
                    elif reflection_action["action"] == "give_up":
                        final_response_text = reflection_action["answer"]
                        print(f"Francine: Giving up on task. Reason: {reflection_action.get('reason', 'LLM gave up')}")
                        log_interaction(prompt, final_response_text)
                        await voice_speak(final_response_text)
                        return # Exit handle_prompt, task given up
                    else:
                        # Fallback if reflection itself returns an invalid action
                        final_response_text = f"I encountered an unexpected issue while trying to self-correct for the failure of '{func_name}'. Error: {tool_error_message}. Please try rephrasing your request."
                        log_interaction(prompt, final_response_text)
                        await voice_speak(final_response_text)
                        return # Exit handle_prompt, unrecoverable error
            else: # LLM did not call a function, or func_name was 'none'
                final_response_text = parsed.get("answer", analysis)
                print(final_response_text)
                log_interaction(prompt, final_response_text)
                await voice_speak(final_response_text)
                return # Exit handle_prompt, task completed (direct answer)

        except Exception as e:
            auto_fix(e)
            error_message = f"An unhandled error occurred during prompt processing: {e}. Please try again."
            print(error_message)
            log_interaction(prompt, f"Unhandled Error: {e}")
            await voice_speak(error_message)
            return # Exit handle_prompt, unrecoverable error

    # If loop finishes without success after all retries
    final_response_text = f"I'm sorry, I tried to fulfill your request '{prompt}' multiple times but encountered persistent issues. Please try rephrasing your request or check the logs for more details."
    print(final_response_text)
    log_interaction(prompt, final_response_text)
    await voice_speak(final_response_text)


# --- NEW: Feedback Mode Handler (from your provided main.py) ---
# This function is called if the prompt matches the self-correction regex
async def handle_feedback_request(prompt: str, core_memory: str, constitution: str):
    """Generates two responses and asks the user for feedback."""
    print("--- Entering Feedback Mode ---")
    try:
        prompt1_instruction = (
            f"--- CONSTITUTION ---\n{constitution}\n--- CORE MEMORY ---\n{core_memory}\n"
            "Style guideline: Be extremely concise and direct.\n"
            f"User query: {prompt}"
        )
        prompt2_instruction = (
            f"--- CONSTITUTION ---\n{constitution}\n--- CORE MEMORY ---\n{core_memory}\n"
            "Style guideline: Be more detailed and provide explanations.\n"
            f"User query: {prompt}"
        )
        response1, response2 = await asyncio.gather(
            llm.ollama_chat(prompt1_instruction),
            llm.ollama_chat(prompt2_instruction)
        )
        all_responses = [response1, response2]
        feedback_prompt = (
            "I have two possible responses for you. Please choose the one you prefer:\n\n"
            f"[1] {response1}\n\n"
            f"[2] {response2}\n\n"
            "Please enter 1 or 2:"
        )
        print(feedback_prompt)
        await voice_speak("I have two options for you. Please check the console and type your choice.")
        choice = typer.prompt("")
        chosen_response = ""
        if choice == '1':
            chosen_response = response1
        elif choice == '2':
            chosen_response = response2
        else:
            print("Invalid choice. No feedback will be logged.")
            await voice_speak("Invalid choice.")
            return
        print(f"You chose: {chosen_response}")
        await voice_speak(f"Thank you for your feedback.")
        evolution.log_feedback(prompt, chosen_response, all_responses)
    except Exception as e:
        auto_fix(e)
        error_message = f"An error occurred during feedback mode: {e}."
        print(error_message)
        await voice_speak(error_message)


# --- MODIFIED: Main function to integrate evolution and dynamic context ---
def main():
    """Main entry point for the Francine application."""
    print("Starting Francine...")
    
    print("Performing initial reflection on startup to update core memory...")
    asyncio.run(evolution.reflect_on_memory())
    
    speech_mode_enabled = False
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r') as f:
                cfg = json.load(f)
                speech_mode_enabled = cfg.get("speech", False)
        except json.JSONDecodeError:
            print("Francine: Error reading config.json. Defaulting to text chat.")
    else:
        print("Francine: config.json not found. Defaulting to text chat.")

    if speech_mode_enabled:
        print("Francine: Attempting to start in voice mode...")
        try:
            asyncio.run(voice_loop_async())
        except Exception as e:
            auto_fix(e)
            print(f"Francine: Voice mode failed to start. Error: {e}")
            print("Francine is switching to text chat mode.")
            asyncio.run(main_chat_loop())
    else:
        print("Francine: Speech mode is disabled in config.json. Starting in text chat mode.")
        asyncio.run(main_chat_loop())


# --- MODIFIED: Existing chat and voice loops ---
@app.command()
def chat():
    """Start a text chat with Francine."""
    asyncio.run(main_chat_loop())

async def main_chat_loop():
    """Asynchronous loop for text chat interaction."""
    profile = memory.load_user_profile()
    print("Starting Francine in text chat mode.")
    while True:
        user_input = typer.prompt("You")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Francine: Goodbye!")
            break
        await handle_prompt(user_input)
        profile["last_message"] = user_input
        memory.save_user_profile(profile)

async def voice_loop_async():
    """Main asynchronous loop for voice interaction."""
    print("Francine: Voice mode active. Listening...")
    while True:
        try:
            text = await asyncio.to_thread(voice.whisper_listen)
            if text:
                print(f"You (Voice): {text}")
                await handle_prompt(text)
            else:
                await asyncio.sleep(0.1) # Prevent busy-waiting
        except Exception as e:
            auto_fix(e)
            print(f"Francine: An error occurred in voice mode: {e}. Switching to text chat mode.")
            await main_chat_loop()
            break


if __name__ == "__main__":
    main()
