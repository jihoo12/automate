# AI Documentation Generator CLI

This command-line tool generates or updates a `README.md` file using local Large Language Models (LLMs) via Ollama. It analyzes the repository's structure, reads specified files for context, and retrieves Git metadata to generate documentation content.

## Features

*   **Context Gathering:** Traverses the filesystem, reading contents from defined code file types across the repository.
*   **Git Integration:** Executes `git` commands internally to collect system metadata (e.g., current branch).
*   **LLM Interface:** Sends compiled context and data payloads to an Ollama-managed local LLM for text generation.
*   **Execution Control:** Prompts the user before invoking the documentation update process.

## Architecture Overview

The tool is implemented as a Python CLI utility comprising three functional layers:

1.  **Context Generation (`get_project_context`):**
    *   Performs filesystem traversal starting from the current directory.
    *   Reads files matching specified extensions, excluding directories like `.git`, `__pycache__`, `node_modules`, `venv`, and others listed in `ignored_dirs`.
    *   The combined text content is accumulated into a knowledge base for the LLM. The process includes a check to stop context accumulation if the total character count reaches 50,000 characters (`max_total_chars`).

2.  **System Utility Layer (`run_git_command`):**
    *   A wrapper around Python's `subprocess` module used exclusively for executing system commands (specifically Git).
    *   It implements error handling for missing `git` command and non-zero exit codes returned by the executed process.

3.  **Control Flow Layer (`main` execution path):**
    *   Coordinates context gathering, executes necessary git commands, and manages user interaction.
    *   Aggregates code content, git data, and prepares a structured prompt payload for the Ollama client.

## Dependencies & Setup

### Prerequisites

Before running the tool, ensure the following are installed:

1.  **Python:** A stable Python environment (Version 3.8 or higher).
2.  **Ollama:** The Ollama service must be running and accessible from your terminal session.
3.  **Required Libraries:** Install the client library via pip:

```bash
pip install ollama
```

### Usage

1.  **Setup:** Navigate to the root directory of the project containing the `README.md` file you intend to update.
2.  **Execution:** Run the main script from your terminal:

```bash
python main.py
```

### Workflow Explanation (When running `main.py`)

The script executes a deterministic workflow:

1.  **Context Collection:** The system scans specified project files using allowed extensions (`.py`, `.js`, `.ts`, `.go`, etc.), accumulating content into one text block, stopping if the 50,000 character limit is met.
2.  **Git Status Check:** Executes `git` commands to gather current repository metadata.
3.  **User Confirmation:** The script prompts: `Do you want to generate or update README.md? (y/N):`. Inputting `y` is required to proceed.
4.  **Documentation Generation:** The compiled context and git metadata are sent to the local LLM running via Ollama. Upon successful response, the generated Markdown content overwrites or creates the `README.md` file in the current directory.

---

### ⚠️ Technical Constraints & Limitations

*   **Context Truncation:** Code context from individual files is limited by the overall system constraint (`max_total_chars = 50000`).
*   **File Scope:** Context gathering relies strictly on files matching extensions defined in `allowed_extensions` within `main.py`.
*   **Dependencies:** Requires external services: Git must be available via the system PATH, and Ollama must be running (communicating with a host at `http://host.docker.internal:11434`).

## Development / Contribution

This tool requires modification of `main.py` to change functionality.

*   **Modifying Context Scope:** To include different file types, modify the `allowed_extensions` set within the `get_project_context()` function in `main.py`.
*   **Custom Git Handling:** Advanced git operations must be implemented by modifying the structure and parameters passed to the `run_git_command` helper function.