# 🤖 Francine: Your Personal, Local AI Assistant

✨ **Crafted with passion by Jeff Bulger** ✨

Francine is a powerful, open-source AI assistant designed to run entirely on your Windows 11 computer. Built with a strong focus on privacy, efficiency, and local operation, Francine leverages your system's resources to provide a wide range of functionalities without relying on external APIs or incurring any costs.

All Large Language Model (LLM) interactions occur through a local Ollama server, ensuring your data stays securely on your machine. This project has been meticulously refactored for improved responsiveness and resource efficiency, especially for real-time voice interactions, making your experience smoother than ever.

---

## 🌟 Key Features

* **Local LLM Interaction**: Powered by your local Ollama server, Francine intelligently uses `gemma3:12b-it-q4_K_M` for chat and `all-minilm:latest` for efficient embeddings. All AI processing happens directly on your PC.

* **Highly Responsive Voice Interaction**: Enjoy seamless conversations with Francine thanks to integrated Speech-to-Text (Whisper) and Text-to-Speech (`pyttsx3`) capabilities, designed for low-latency responses. Utilizes `webrtcvad-wheels` for efficient Voice Activity Detection (VAD).

* **Comprehensive OSINT Tools**: Gather open-source intelligence on various entities like usernames, emails, people, vehicles, and domains. *(Note: IP lookup via external API has been removed to strictly adhere to the no-cost policy).*

* **E-commerce Helpers**: Get assistance with product research (e.g., scraping data from AliExpress) and analyze TikTok trends. *(Note: Shopify API integration is a non-functional placeholder, ensuring no external costs).*

* **Document Utilities**: Effortlessly read text from PDFs, autofill PDF forms, and even generate new PDFs directly from Markdown content.

* **Efficient Retrieval-Augmented Generation (RAG)**: Enhance Francine's knowledge by letting it "chat" with your own documents. This feature uses a unified local embedding model via Ollama for optimal resource use. Francine also dynamically retrieves relevant context from her constitution and core memories.

* **Job Scheduling**: Automate repetitive tasks at your desired intervals.

* **Local File Management**: Francine can interact with your local file system (list, read, write, move, delete files/directories) within a **designated safe folder** on your desktop.

* **Web Automation**: Francine can navigate websites and fill out forms using local browser control (powered by Playwright).

* **Persistent Memory & Personality**: Francine remembers past interactions, user preferences, and her core principles (constitution), storing all this data locally. She can also self-correct from tool failures and ask for clarification.

---

## 🚀 Setup: Get Francine Running (The Streamlined Way!)

Getting Francine set up is now streamlined into a few clear steps. Follow these to bring your personal AI assistant to life:

1.  ### Clone this Repository

    Download the entire Francine project to your computer. The easiest way is to click the green **`Code`** button on GitHub and select **`Download ZIP`**. Once downloaded, extract the contents to a convenient location on your machine (e.g., your Desktop).

    * *Example Path*: `C:\Users\YourUsername\Desktop\Your-Francine-Project-Folder`
        ➡️ **IMPORTANT:** Remember to replace `YourUsername` with your actual Windows username in any file paths mentioned in this README!

    <!-- You can add an image here, like a screenshot of the folder structure or Francine running! -->
    <!-- Example: ![Francine Folder Structure](path/to/your/image.png) -->
    <!-- Or a placeholder: -->
    ![Francine Screenshot/Diagram](https://placehold.co/600x300/ADD8E6/000000?text=Your+Francine+Image+Here)
    *Replace this placeholder with an actual image showcasing Francine or its setup!*

2.  ### Create Python Virtual Environment (Manual Prerequisite)

    This is the **only manual step** required before running the installer script. It ensures your Python environment is set up correctly.

    * **Open your Command Prompt or PowerShell window** (you do NOT need administrator privileges for this step).
    * **Navigate to your Francine project folder**. If you extracted to `C:\Users\YourUsername\Desktop\Your-Francine-Project-Folder`, then:
        ```bash
        cd C:\Users\YourUsername\Desktop\Your-Francine-Project-Folder
        ```
    * **Run the command to create the virtual environment:**
        ```bash
        python -m venv venv
        ```
        This will create a new folder named `venv` in your project directory.

3.  ### Run the Automated Installer (`install_francine.py`)

    This script will handle the rest of the installation process automatically.

    * **Close** the Command Prompt/PowerShell window you used for Step 2.
    * **Open a *new* Command Prompt or PowerShell window AS AN ADMINISTRATOR.**
        * **⚠️ IMPORTANT**: You **must** run your terminal **as an administrator** for the installers (Tesseract, Ollama) to work correctly. To do this, right-click on "Command Prompt" or "PowerShell" in your Start Menu and select **"Run as administrator."**
    * **Navigate to your Francine project folder** in the administrator terminal:
        ```bash
        cd C:\Users\YourUsername\Desktop\Your-Francine-Project-Folder
        ```
    * **Run the installer script:**
        ```bash
        python install_francine.py
        ```
    * **Follow the Prompts**: This script is smart! It will guide you through the process:
        * It will **Check for Tesseract OCR**: If Tesseract is not found on your system, it will download and **launch the Tesseract installer**. You will need to **follow the on-screen instructions** of the Tesseract installer (clicking "Next," "Install," etc.) and then **press Enter** in your terminal when you've completed its setup.
        * It will **Check for Ollama**: If the Ollama server isn't running on your machine, it will download and **launch the Ollama installer**. Again, you will need to **follow the on-screen instructions** of the Ollama installer and then **press Enter** in your terminal once you've completed its setup and confirmed the server is running.
        * It will **Pull Ollama Models**: After Ollama is confirmed running, the script will automatically download the necessary `gemma3:12b-it-q4_K_M` and `all-minilm:latest` models from Ollama's library.
        * It will **Install Python Packages**: All required Python libraries (listed in `requirements.txt`) will be installed directly into your new virtual environment.
        * It will **Install Playwright Browsers**: It will download the essential browser binaries (Chromium, Firefox, WebKit) that Playwright uses for web automation.
        * It will **Create Base Directories**: Finally, it will set up the necessary data folders for Francine, located at `C:\Users\YourUsername\FrancineData` (this is where logs, RAG index, and raw data will be stored).
            ➡️ **IMPORTANT:** This path is now dynamic, so it will automatically go into your user's home directory.
        * It will **Build the RAG Index**: This is done automatically at the end of the installation.

4.  ### Prepare RAG Documents (Optional but Recommended)

    If you want Francine to "chat with your documents" using its Retrieval-Augmented Generation (RAG) feature:

    * Create a new folder named `documents_to_index` inside `C:\Users\YourUsername\FrancineData`.
        ➡️ **IMPORTANT:** Remember to replace `YourUsername` with your actual Windows username in this path!

    * Place all your plain text documents (`.txt` files) that you want Francine to learn from into this `documents_to_index` folder.

5.  ### Configure Voice Mode (Optional)

    By default, Francine starts in text chat mode. To enable voice interaction:

    * Create a new file named `config.json` in your main Francine project folder (the same directory as `main.py` and `start_francine.bat`).
    * Add the following content to `config.json`:

        ```json
        {
            "speech": true
        }
        ```

    * If `config.json` is absent or the `"speech"` value is `false`, Francine will start in text chat mode.

---

## ▶️ Usage: Starting Francine

Once the setup is complete, starting Francine is a single click:

* **Launch Francine**: Simply **double-click the `start_francine.bat` file** located in your main Francine project folder.
    * This script will automatically activate the virtual environment and launch `main.py`.
    * Francine will then check your `config.json` to determine if it should start in voice or text chat mode.

---

## ⚙️ Architecture & Efficiency Notes

Francine's backend has been meticulously refactored to use `asyncio` for highly efficient multitasking. This means it can perform complex operations (like LLM inference or web browsing) concurrently without freezing, providing a smoother, lower-latency experience, especially for real-time voice interactions. We've also unified the embedding model to `all-minilm:latest` via Ollama, significantly reducing its memory footprint for optimal resource utilization on your PC.

---

## ⚠️ **Important Security & Usage Notes** ⚠️

* **Python Version**: Francine requires **Python 3.10 or newer** for full compatibility with features like `Path.is_relative_to` used for file sandboxing. Ensure you have an up-to-date Python installation.

* **File Manager Access**: Francine's file management tools are restricted to the `C:\Users\YourUsername\FrancineData\ManagedFiles` directory by default. If you change this `BASE_FILE_ACCESS_DIR` in `file_manager.py` to a broader path (e.g., `Path.home() / "Desktop"`), be aware that an LLM misinterpretation of a command could lead to unintended file modifications or deletions. **Use with caution and always back up important data.**

* **Web Scraping (`scrape_text_content`)**: This tool can be instructed to visit any URL. While it's powerful, be cautious about instructing Francine to visit unknown or malicious websites, as this carries inherent web browsing risks.

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file in this repository for full details.
