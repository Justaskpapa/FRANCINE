import subprocess
import sys
import os
from pathlib import Path
import json
import time
import requests
import shutil  # For deleting temporary files
import asyncio  # For running async RAG index build

# --- Configuration ---
# FIX: Dynamically determine BASE_DIR based on user's home directory for portability
# This will create a 'FrancineData' folder inside the user's home directory.
# We import memory here to use its BASE_DIR definition
try:
    import memory
    BASE_DIR = memory.BASE_DIR
except ImportError:
    # Fallback if memory.py isn't available yet (e.g., during initial script execution before all files are in place)
    BASE_DIR = Path.home() / "FrancineData"
    print(f"Warning: memory.py not fully loaded. Defaulting BASE_DIR to {BASE_DIR}")

FRANCINE_DIRS = [
    BASE_DIR / "raw_hits",
    BASE_DIR / "faiss_idx",
    BASE_DIR / "logs",
    BASE_DIR / "ManagedFiles",  # Ensure the managed files directory is created
    BASE_DIR / "documents_to_index"  # Ensure the RAG documents directory is created
]

# Virtual Environment Configuration
VENV_DIR = Path("./venv")  # Virtual environment will be created in a 'venv' folder
VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"  # Path to Python executable inside venv

# Download URLs for external software (these might change over time!)
TESSERACT_INSTALLER_URL = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.0.20221222.exe"
TESSERACT_INSTALLER_FILENAME = "tesseract-ocr-setup.exe"

OLLAMA_INSTALLER_URL = "https://ollama.com/download/windows"
OLLAMA_INSTALLER_FILENAME = "OllamaSetup.exe"

# Required Ollama models
REQUIRED_OLLAMA_MODELS = ["gemma3:12b-it-q4_K_M", "all-minilm:latest"]

# --- Helper Functions ---
def run_command(command, message, check_output=False, shell=False, executable=None):
    """
    Helper function to run shell commands and provide feedback.
    'executable' can be used to specify a specific python.exe (e.g., from a venv).
    """
    print(f"\n--- {message} ---")
    try:
        if executable:
            cmd_list = [str(executable)] + [str(arg) for arg in command] if isinstance(command, (list, tuple)) else [str(executable)] + [str(arg) for arg in command.split()]
        elif isinstance(command, str):
            cmd_list = command
            shell = True
        else:
            cmd_list = [str(arg) for arg in command]

        process = subprocess.run(cmd_list, check=True, capture_output=True, text=True, shell=shell)

        if check_output:
            return process.stdout.strip()
        print(process.stdout)
        if process.stderr:
            print("Errors/Warnings (if any):\n", process.stderr)
        print(f"--- {message} completed successfully. ---")
        return True
    except subprocess.CalledProcessError as e:
        print(f"--- ERROR: {message} failed ---")
        print(f"Command: {' '.join(e.cmd) if isinstance(e.cmd, list) else e.cmd}")
        print(f"Return Code: {e.returncode}")
        print(f"STDOUT:\n{e.stdout}")
        print(f"STDERR:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print(f"--- ERROR: Command not found. Make sure necessary executables are in your PATH or specified. ---")
        return False
    except Exception as e:
        print(f"--- UNEXPECTED ERROR during '{message}': {e} ---")
        return False

def download_file(url, filename):
    """Downloads a file from a URL to the current directory."""
    print(f"Downloading {filename} from {url}...")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded {filename}.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to download {filename}: {e}")
        return False
    except Exception as e:
        print(f"UNEXPECTED ERROR during download of {filename}: {e}")
        return False

# --- Check and Install Functions ---
TESSERACT_DEFAULT_PATH = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")

def check_tesseract():
    """Checks if Tesseract OCR is installed and accessible by its default path."""
    print("\n--- Checking for Tesseract OCR ---")
    if TESSERACT_DEFAULT_PATH.exists():
        try:
            result = run_command([str(TESSERACT_DEFAULT_PATH), "--version"], "Checking Tesseract version", shell=False)
            if result:
                print("Tesseract OCR found at default path:")
                return True
            else:
                print("Tesseract OCR found at default path but failed to run version check.")
                return False
        except Exception as e:
            print(f"Error checking Tesseract at default path: {e}")
            return False
    else:
        print(f"Tesseract OCR not found at default path: {TESSERACT_DEFAULT_PATH}.")
        return False

def install_tesseract():
    """Downloads and attempts to install Tesseract OCR (with GUI)."""
    print("\n--- Attempting to install Tesseract OCR ---")
    installer_path = Path(TESSERACT_INSTALLER_FILENAME)
    if not installer_path.exists():
        if not download_file(TESSERACT_INSTALLER_URL, TESSERACT_INSTALLER_FILENAME):
            print("Failed to download Tesseract installer. Please download and install manually.")
            return False

    print("Running Tesseract installer (may require UAC prompt and user interaction)...")
    installer_process = subprocess.Popen([str(installer_path)], creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    
    try:
        print("Tesseract installer launched. Please follow the on-screen instructions to complete the installation.")
        input("Press Enter AFTER you have completed Tesseract OCR installation and its window has closed...")
        
        for _ in range(10):
            if TESSERACT_DEFAULT_PATH.exists():
                print("Tesseract OCR executable detected after installation.")
                return True
            time.sleep(1)
        print("Tesseract OCR executable not found after installation. Please check the installation manually.")
        return False
    except Exception as e:
        print(f"Error during Tesseract installation process: {e}")
        return False
    finally:
        if installer_path.exists():
            try:
                os.remove(installer_path)
                print(f"Cleaned up {installer_path}")
            except Exception as e:
                print(f"Warning: Could not delete installer file {installer_path}: {e}")

OLLAMA_DEFAULT_PATH = Path(os.getenv("LOCALAPPDATA")) / "Programs" / "Ollama" / "ollama.exe"

def check_ollama_server():
    """Checks if Ollama server is running."""
    print("\n--- Checking for Ollama Server ---")
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        response.raise_for_status()
        print(f"Ollama server found and running at {ollama_host}.")
        return True
    except requests.exceptions.ConnectionError:
        print(f"Ollama server not found or not running at {ollama_host}.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error checking Ollama server: {e}")
        return False

def install_ollama():
    """
    Attempts to start Ollama if installed, otherwise downloads and installs it.
    """
    print("\n--- Attempting to install or start Ollama ---")

    # 1. Try to start Ollama if it exists but isn't running
    if OLLAMA_DEFAULT_PATH.exists():
        print(f"Ollama executable found at {OLLAMA_DEFAULT_PATH}. Attempting to start server...")
        try:
            subprocess.Popen([str(OLLAMA_DEFAULT_PATH), "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP, shell=True)
            print("Ollama serve command issued. Waiting for server to become responsive...")
            for _ in range(30):
                if check_ollama_server():
                    print("Ollama server started and verified.")
                    return True
                time.sleep(1)
            print("Ollama server did not become responsive after starting. Proceeding with fresh installation attempt.")
        except Exception as e:
            print(f"Error starting Ollama server from existing install: {e}. Proceeding with fresh installation attempt.")
    else:
        print(f"Ollama executable not found at {OLLAMA_DEFAULT_PATH}. Proceeding with download and installation.")

    # 2. If not found or failed to start, proceed with fresh installation
    installer_path = Path(OLLAMA_INSTALLER_FILENAME)
    if installer_path.exists():
        os.remove(installer_path)
        print(f"Removed old installer: {installer_path}")
    
    if not download_file(OLLAMA_INSTALLER_URL, OLLAMA_INSTALLER_FILENAME):
        print("Failed to download Ollama installer. Please download and install manually.")
        return False

    print("Running Ollama installer (may require UAC prompt and user interaction)...")
    installer_process = subprocess.Popen([str(installer_path)], creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)

    try:
        print("Ollama installer launched. Please follow the on-screen instructions to complete the installation.")
        input("Press Enter AFTER you have completed Ollama installation and its window has closed...")
        for _ in range(30):
            if check_ollama_server():
                print("Ollama server started and verified.")
                return True
            time.sleep(1)
        print("Ollama server did not start in time after installation. Please check the installation manually.")
        return False
    except Exception as e:
        print(f"Error during Ollama installation process: {e}")
        return False
    finally:
        if installer_path.exists():
            try:
                os.remove(installer_path)
                print(f"Cleaned up {installer_path}")
            except Exception as e:
                print(f"Warning: Could not delete installer file {installer_path}: {e}")

def pull_ollama_models():
    """Pulls required Ollama models if missing."""
    print("\n--- Pulling required Ollama models ---")
    
    if not check_ollama_server():
        print("Ollama server is not running. Cannot pull models. Please ensure Ollama is installed and running.")
        return False

    ollama_command_path = Path(os.getenv("LOCALAPPDATA")) / "Programs" / "Ollama" / "ollama.exe"
    ollama_command = str(ollama_command_path) if ollama_command_path.exists() else "ollama"

    installed_models_output = run_command([ollama_command, "list"], "Listing Ollama models", check_output=True, shell=False)
    if installed_models_output is False:
        print("Could not list Ollama models. Ollama command might not be in PATH or server not running.")
        return False

    installed_models = []
    for line in installed_models_output.splitlines():
        if ':' in line and len(line.split()) > 1:
            model_name = line.split()[0]
            installed_models.append(model_name)

    all_models_present = True
    for model in REQUIRED_OLLAMA_MODELS:
        if model not in installed_models:
            print(f"Missing model: {model}. Attempting to pull...")
            success = run_command([ollama_command, "pull", model], f"Pulling Ollama model: {model}", shell=False)
            if not success:
                print(f"ERROR: Failed to pull model {model}. Please try manually: `ollama pull {model}`")
                all_models_present = False
        else:
            print(f"Model {model} is already present.")
    
    return all_models_present

def ensure_playwright_browsers():
    """
    Installs Playwright’s browser bundles (Chromium / Firefox / WebKit).
    Safe to run every time – if they’re already present it exits instantly.
    """
    return run_command(
        [str(VENV_PYTHON), "-m", "playwright", "install", "--with-deps"],
        "Installing Playwright browsers (idempotent)",
        shell=False
    )

def install_python_requirements():
    """Handles installation of Python requirements into the virtual environment."""
    script_dir = Path(__file__).parent
    requirements_file = script_dir / "requirements.txt" 
    
    if not requirements_file.exists():
        requirements_file = script_dir.parent / "requirements.txt"
        if not requirements_file.exists():
            print(f"ERROR: 'requirements.txt' not found in '{script_dir}' or '{script_dir.parent}'.")
            print("Please make sure requirements.txt is at the root of your project.")
            sys.exit(1)

    print("\n--- Installing Python requirements into virtual environment ---")
    # FIX: Check if VENV_PYTHON is functional before trying to use it
    if not VENV_PYTHON.exists():
        print(f"ERROR: Python executable not found in virtual environment: {VENV_PYTHON}")
        print("The virtual environment appears to be corrupted or not created. Please create it manually:")
        print(f"  cd {Path.cwd()}")
        print(f"  python -m venv venv")
        print("Then run this installer script again.")
        sys.exit(1) # Exit if venv is not functional

    # FIX: Use run_command with explicit executable for pip install
    run_command([str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip"], "Upgrading pip in venv", shell=False)
    run_command([str(VENV_PYTHON), "-m", "pip", "install", "-r", str(requirements_file)], "Installing Python packages into venv", shell=False)
    return True

def check_and_create_francine_dirs():
    """Checks and creates Francine's base directories."""
    print("\n--- Checking Francine's Base Directories ---")
    all_exist = True
    for d in FRANCINE_DIRS:
        if not d.exists():
            print(f"Creating directory: {d}")
            d.mkdir(parents=True, exist_ok=True)
            all_exist = False
        else:
            print(f"Directory already exists: {d}")
    if all_exist:
        print("All Francine base directories already exist.")
    else:
        print("Francine base directories checked/created.")
    return True

def install_francine_orchestrator():
    """Orchestrates the automated installation of all Francine dependencies."""
    print("--- Starting Francine Automated Setup Orchestrator ---")
    print("NOTE: This script may trigger User Account Control (UAC) prompts for external installers.")
    print("Please grant necessary permissions if prompted.")
    print("You will need to interact with the Tesseract and Ollama installers if they launch.")

    # 1. Check/Install Tesseract OCR
    if not check_tesseract():
        if not install_tesseract():
            print("\n--- Tesseract OCR installation failed or could not be verified. Please install manually. ---")
            sys.exit(1)

    # 2. Check/Install Ollama Server
    if not install_ollama(): # This function now handles both starting and installing
        print("\n--- Ollama setup failed or could not be verified. Please check manually. ---")
        sys.exit(1)
    
    # 3. Pull Ollama Models (only if server is running)
    if not pull_ollama_models():
        print("\n--- Some Ollama models could not be pulled. Please check your Ollama installation and try `ollama pull` manually. ---")
        # Do not exit here, as Francine might still run with chat, just not fully functional RAG/LLM
        
    # 4. Install Python requirements (including playwright library)
    # FIX: This section now assumes venv is already created and functional
    print("\n--- Setting up Python Virtual Environment ---")
    if not VENV_DIR.exists():
        print(f"ERROR: Virtual environment not found at {VENV_DIR}.")
        print("Please create it manually first by running:")
        print(f"  cd {Path.cwd()}")
        print(f"  python -m venv venv")
        print("Then run this installer script again.")
        sys.exit(1)
    
    # After confirming venv exists, proceed with installing requirements into it
    if not install_python_requirements():
        print("\n--- Python requirements installation failed. Please check your Python/pip setup. ---")
        sys.exit(1)

    # 5. Ensure Playwright browsers are present
    if not ensure_playwright_browsers():
        print("\n--- Playwright browser installation failed. "
              "Run  venv\\Scripts\\python.exe -m playwright install --with-deps  manually. ---")

    # 6. Check/Create Francine's base directories
    check_and_create_francine_dirs()

    # FIX: Automatically build RAG index after all installations are done
    print("\n--- Building RAG Index (This may take a moment) ---")
    try:
        import sys, pathlib
        repo_root = next(p for p in pathlib.Path(__file__).resolve().parents
                         if (p / "rag.py").exists())
        sys.path.insert(0, str(repo_root))     # <- NOW Python sees rag.py

        import rag
        asyncio.run(rag.build_rag_index())
        print("RAG Index built successfully.")
    except Exception as e:
        print(f"ERROR: Failed to build RAG Index. Francine cannot run without her long-term memory. Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n--- Francine Automated Setup Complete! ---")
    print("Francine should now be ready to run. You can start it using the 'start_francine.bat' script.")
    print("\nIf you encounter issues, please refer to the README.md and error messages above.")

if __name__ == "__main__":
    install_francine_orchestrator()
