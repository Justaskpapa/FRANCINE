import subprocess
import sys
from pathlib import Path
import os
import time

# --- Configuration ---
VENV_DIR = Path("./venv") # Virtual environment will be created in a 'venv' folder
VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe" # Path to Python executable inside venv

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

def create_and_install_python_env():
    """Creates a virtual environment and installs Python packages into it."""
    
    # FIX: Ensure requirements_file is defined before its existence is checked
    script_dir = Path(__file__).parent
    requirements_file = script_dir / "requirements.txt" 

    # If script is in a subfolder (e.g., 'Francine/'), check parent for requirements.txt
    if not requirements_file.exists():
        requirements_file = script_dir.parent / "requirements.txt"
        if not requirements_file.exists():
            print(f"ERROR: 'requirements.txt' not found in '{script_dir}' or '{script_dir.parent}'.")
            print("Please make sure requirements.txt is at the root of your project.")
            sys.exit(1)

    print("\n--- Setting up Python Virtual Environment ---")
    if not VENV_DIR.exists():
        print(f"Creating virtual environment at {VENV_DIR}...")
        success = run_command(f'"{sys.executable}" -m venv "{VENV_DIR}"', "Creating venv", shell=True)
        if not success:
            print("Failed to create virtual environment. Please check your Python installation.")
            sys.exit(1)
        print("Virtual environment created.")
    else:
        print("Virtual environment already exists.")

    if not VENV_PYTHON.exists():
        print(f"ERROR: Python executable not found in virtual environment: {VENV_PYTHON}")
        print("Virtual environment setup failed. This is critical for installing packages.")
        sys.exit(1)

    print("\n--- Installing Python requirements into virtual environment ---")
    run_command([str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip"], "Upgrading pip in venv", shell=False)
    run_command([str(VENV_PYTHON), "-m", "pip", "install", "-r", str(requirements_file)], "Installing Python packages into venv", shell=False)
    
    print("\n--- Python Environment Setup Complete! ---")
    print("Virtual environment created and requirements installed.")

if __name__ == "__main__":
    create_and_install_python_env()
