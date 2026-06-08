# AI Documentation Generator CLI

This command-line tool automates the process of creating or updating a `README.md` file by leveraging local Large Language Models (LLMs) via Ollama. It analyzes the existing codebase structure, reads key files for context, and utilizes Git information to generate comprehensive, up-to-date project documentation.

## ✨ Features

*   **Automated Context Gathering:** Scans specified file types (`.py`, `.js`, `.ts`, etc.) across the repository to understand the project's functionality.
*   **Git Awareness:** Executes `git` commands internally to gather metadata (e.g., current branch, last commit) ensuring the README reflects the latest state of the code.
*   **LLM Integration:** Seamlessly integrates with local LLMs running through Ollama for natural language documentation generation.
*   **Interactive Workflow:** Prompts the user to initiate the documentation update process safely.

## 🏗️ Architecture

The tool is built as a simple Python CLI utility following the Model-View-Controller (MVC) pattern conceptually:

1.  **Context Layer (`get_project_context`):** Responsible for filesystem traversal. It walks through the current directory, selectively reading code files while ignoring common build/virenv directories (`.git`, `node_modules`, etc.). This compiled text serves as the knowledge base for the AI.
2.  **Utility Layer (`run_git_command`):** Acts as a wrapper around Python's `subprocess` module to execute system commands (specifically Git). It handles critical error checking (e.g., ensuring Git is installed, catching non-zero exit codes) and ensures robust failure handling.
3.  **Control Flow Layer (`handle_readme`):** Manages the user interaction loop. It aggregates the gathered context (code files + git data), prompts the user for action, and structures the final prompt payload sent to the Ollama client.

### Dependencies

*   Python 3.8+
*   Ollama running locally
*   `ollama` Python Client Library

## 🚀 Prerequisites

Before running the tool, ensure you have the following installed:

1.  **Python:** A stable Python environment (3.8 or higher).
2.  **Ollama:** The Ollama service must be running in the background and accessible from your terminal session.
3.  **Required Libraries:** Install the necessary client library via pip:

```bash
pip install ollama
```

## ⚙️ Usage

### 1. Setup

Navigate to the root directory of the project you wish to document.

### 2. Execution

Run the main script from your terminal:

```bash
python main.py
```

### 3. Documentation Generation Workflow

The script will execute the following steps internally:

1.  **Context Collection:** It scans all relevant files, accumulating a large block of code context.
2.  **Git Status Check:** It gathers current repository status (branch, commit history).
3.  **Prompting User:** A prompt will appear: `Do you want to generate or update README.md? (y/N):`
4.  **Confirmation:** Enter `y` and press Enter to proceed with calling the LLM.

The script then sends a consolidated, comprehensive prompt to your local Ollama model, which generates the Markdown content, updating or creating `README.md` in the current directory.

---

### ⚠️ Troubleshooting

*   **"Error: 'git' command not found."**: Ensure Git is installed on your system and accessible via your system PATH.
*   **Ollama Connection Error**: Verify that the Ollama service is running (`ollama run llama2` or similar test) before executing `main.py`.
*   **Context Truncation:** Due to limitations, files are truncated (the first 2000 characters) when collecting context; this prevents memory overflow but might cause loss of detail in extremely large source files.

## 💡 Development / Contribution

This tool is designed to be run within the project directory. If you plan to extend its functionality:

*   **Modifying Context Scope:** Change the `allowed_extensions` set in `get_project_context()` to include other file types (e.g., Markdown assets, documentation files).
*   **Custom Git Handling:** Enhance the `run_git_command` helper if specific git operations are required beyond standard status checking.