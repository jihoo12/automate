# AI Documentation Generator CLI

This command-line tool automates the process of creating or updating a `README.md` file by leveraging local Large Language Models (LLMs) via Ollama. It analyzes the existing codebase structure, reads key files for context, and utilizes Git information to generate comprehensive, up-to-date project documentation.

## ✨ Features

*   **Automated Context Gathering:** Scans specified file types (`.py`, `.js`, `.ts`, etc.) across the repository to understand the project's functionality.
*   **Git Awareness:** Executes `git` commands internally to gather metadata (e.g., current branch, last commit) ensuring the README reflects the latest state of the code.
*   **LLM Integration:** Seamlessly integrates with local LLMs running through Ollama for natural language documentation generation.
*   **Interactive Workflow:** Prompts the user to initiate the documentation update process safely.

## 🏗️ Architecture Overview

The tool is built as a Python CLI utility conceptually following the Model-View-Controller (MVC) pattern:

1.  **Context Layer (`get_project_context`):**
    *   Responsible for filesystem traversal. It walks through the current directory, selectively reading code files while ignoring common build/virenv directories (`.git`, `node_modules`, etc.).
    *   This compiled text serves as the knowledge base for the AI. **Note:** To manage memory and prevent excessive context bloat, each file's content is truncated after the first 2000 characters.

2.  **Utility Layer (`run_git_command`):**
    *   Acts as a robust wrapper around Python's `subprocess` module to execute system commands (specifically Git).
    *   It handles critical error checking, ensuring Git is installed and providing comprehensive failure handling for non-zero exit codes.

3.  **Control Flow Layer (`handle_readme`):**
    *   Manages the user interaction loop. It aggregates all gathered context (code files + git data), prompts the user for action, and structures the final prompt payload sent to the Ollama client.

## 🛠 Dependencies & Setup

### Prerequisites

Before running the tool, ensure you have the following installed:

1.  **Python:** A stable Python environment (3.8 or higher).
2.  **Ollama:** The Ollama service **must be running** in the background and accessible from your terminal session.
3.  **Required Libraries:** Install the necessary client library via pip:

```bash
pip install ollama
```

### Usage

1.  **Setup:** Navigate to the root directory of the project you wish to document.
2.  **Execution:** Run the main script from your terminal:

```bash
python main.py
```

### Workflow Explained (What happens when you run `main.py`):

The script executes a structured workflow to gather all necessary information before invoking the LLM:

1.  **Context Collection:** Scans all relevant project files (`.py`, `.js`, etc.), accumulating code context into a single large text block.
2.  **Git Status Check:** Executes `git` commands to gather current repository status (e.g., branch, commit history).
3.  **User Confirmation:** A prompt will appear: `Do you want to generate or update README.md? (y/N):`. **You must enter `y`** and press Enter to proceed with calling the LLM.
4.  **Documentation Generation:** The script sends a consolidated, comprehensive prompt containing all gathered context and metadata to your local Ollama model. The model then generates the new Markdown content, which updates or creates the `README.md` file in the current directory.

---

### ⚠️ Troubleshooting & Limitations

*   **"Error: 'git' command not found."**: Ensure Git is installed on your system and accessible via your system PATH environment variable.
*   **Ollama Connection Error**: Verify that the Ollama service is running (`ollama run llama2` or similar test) *before* executing `main.py`.
*   **Context Truncation:** Due to resource management, code context from individual files is limited (truncated after 2000 characters). This prevents memory overflow but means extremely large source files might lose some detail.

## 💡 Development / Contribution

This tool is designed to be run within the project directory. If you plan to extend its functionality:

*   **Modifying Context Scope:** To include different file types (e.g., documentation assets, specialized formats), modify the `allowed_extensions` set inside the `get_project_context()` function in `main.py`.
*   **Custom Git Handling:** Enhance the `run_git_command` helper if specific advanced git operations are required beyond standard status checking and basic error handling.