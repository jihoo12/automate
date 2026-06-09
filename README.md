# AI Documentation Generator CLI

A command-line utility implemented in Python that generates or updates a `README.md` file using local Large Language Models (LLMs) accessed via Ollama. It collects project context by traversing the filesystem, reading files based on defined extensions, and executing system Git commands to gather repository metadata.

## Features

*   **Filesystem Traversal:** Reads contents from files matching defined allowed extensions (`allowed_extensions` set).
*   **Context Truncation Control:** Limits the total accumulated text context to a maximum of 50,000 characters (`max_total_chars`).
*   **Version Control Integration:** Executes `git` commands via Python's `subprocess` module to retrieve repository metadata.
*   **LLM Interaction Layer:** Sends structured payloads containing collected code and Git data to an Ollama client connection.

## Architecture Overview

The utility operates within a Python CLI structure, utilizing the following core functions and components:

### 1. Context Generation (`get_project_context`)
This function performs filesystem traversal starting from the current working directory (`.`).
*   **Directory Exclusion:** It explicitly excludes directories matching `ignored_dirs`: `.git`, `__pycache__`, `node_modules`, `venv`, `.venv`, `env`, `dist`, and `build`.
*   **File Inclusion:** It reads files whose extensions are present in the `allowed_extensions` set (e.g., `.py`, `.js`, `.ts`, `.go`, etc.).
*   **Data Limiting:** Content accumulation stops when the total character count reaches 50,000 characters (`max_total_chars`).

### 2. System Utility Layer (`run_git_command`)
This helper function wraps `subprocess.run()` to execute mandatory system commands (specifically `git`). It handles two defined exceptions:
*   `FileNotFoundError`: Raised if the `git` command is not found on the system PATH.
*   `subprocess.CalledProcessError`: Raised if the executed Git process returns a non-zero exit code.

### 3. Markdown Sanitization (`clean_markdown_block`)
A utility function uses regular expressions to strip markdown code block wrappers (e.g., ` ```optional_language_name ... ``` `) from raw LLM output, extracting only the inner content.

### Execution Flow
The main execution path coordinates context gathering via `get_project_context()`, executes Git commands using `run_git_command()`, and sends the resulting combined payload to the Ollama client. Before proceeding with generation, the utility requires explicit user confirmation (`y/N`).

## Dependencies & Setup

### Prerequisites
The following components must be available:
1. **Python:** A stable Python environment (version not specified).
2. **Ollama Service:** The local LLM host service must be running and accessible at `http://host.docker.internal:11434`.
3. **System Utility:** The `git` command must be available via the system PATH.

### Dependencies Installation
Run the following command to install required client libraries:

```bash
pip install ollama
```

## Usage

1.  **Environment Setup:** Ensure the terminal session can access the Ollama service and the repository is initialized with Git.
2.  **Execution:** Execute the main script from the project root directory:

```bash
python main.py
```

### Workflow Details (Upon running `main.py`)

1. **Context Collection:** The utility traverses files matching defined extensions. Content accumulation stops when 50,000 characters are reached or all allowed files have been processed.
2. **Git Status Check:** Executes internal Git commands to gather current repository metadata.
3. **User Confirmation:** Prints the prompt: `Do you want to generate or update README.md? (y/N):`. Inputting `y` is required to proceed.
4. **Generation:** Sends the accumulated code context and git data to the local LLM. Upon receiving a response, the utility strips markdown wrappers using `clean_markdown_block()` and writes the resulting content to `README.md`, overwriting existing content if necessary.

## Technical Constraints & Scope

*   **Context Limit:** The total text context provided to the LLM is constrained by `max_total_chars = 50000`.
*   **Allowed Files:** Context collection is limited strictly to file types listed in `allowed_extensions` within `main.py`.
*   **External Services:** Requires connectivity to Ollama at `http://host.docker.internal:11434` and access to the system Git executable.

## Development / Contribution

Modification of functionality requires changes within `main.py`.

*   **Modifying Context Scope:** Update the `allowed_extensions` set to include or exclude file types for context collection.
*   **Excluding Directories:** Modify the `ignored_dirs` set within `get_project_context()` function.
*   **Custom Git Handling:** Advanced operations require modifying the arguments passed to `run_git_command(args, error_msg)`.