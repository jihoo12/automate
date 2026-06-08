import os
import sys
import subprocess
import re
from ollama import Client

# Configuration Constants
OLLAMA_HOST = 'http://host.docker.internal:11434'
MODEL_NAME = 'gemma4'
TIMEOUT_SECONDS = 120  # Generous timeout for local LLM generation

def run_git_command(args, error_msg):
    """Helper to run git commands safely with error handling."""
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {error_msg}\nDetails: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'git' command not found. Is it installed?", file=sys.stderr)
        sys.exit(1)

def clean_markdown_block(text):
    """Safely strips markdown code block wrappers (``` or ```markdown) using regex."""
    text = text.strip()
    # Matches ```optional_language_name ... ``` capturing the inside content
    cleaned = re.sub(r'^```[a-zA-Z]*\n?(.*?)\n?```$', r'\1', text, flags=re.DOTALL)
    return cleaned.strip()

def get_project_context():
    """Reads project text files to give the AI context for writing/updating README."""
    context = ""
    ignored_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', 'env', 'dist', 'build'}
    allowed_extensions = {
        '.py', '.js', '.ts', '.go', '.rs', '.json', '.sh', 
        '.yml', '.yaml', '.txt', '.html', '.hs', '.md', '.css'
    }
    
    # Track character count to avoid overwhelming local LLM context windows
    max_total_chars = 50000 
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for file in files:
            if len(context) >= max_total_chars:
                break
                
            _, ext = os.path.splitext(file)
            if ext in allowed_extensions:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        file_content = f.read(2000) # Limit size per file
                        context += f"\n--- File: {file_path} ---\n{file_content}\n"
                except Exception:
                    pass # Gracefully skip unreadable files
                    
    return context

def handle_readme(client):
    """Asks the user if they want to create/update the README using defensive AI context."""
    user_choice = input("\nDo you want to generate or update README.md defensively? (y/N): ").lower().strip()
    if user_choice != 'y':
        return

    readme_path = "README.md"
    readme_exists = os.path.exists(readme_path)
    
    existing_readme_content = ""
    if readme_exists:
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                existing_readme_content = f.read()
        except Exception as e:
            print(f"Warning: Could not read existing README: {e}")

    print("Gathering local file structure context...")
    project_code = get_project_context()

    # --- DEFENSIVE PROMPT BASE ---
    defensive_rules = (
        "\n\nCRITICAL DEFENSIVE WRITING RULES:\n"
        "1. DO NOT extrapolate, assume, or guess functionality. If a feature or variable's purpose is not "
        "explicitly clear from the source code, DO NOT mention it or invent a purpose.\n"
        "2. AVOID ALL AMBIGUOUS WORDS. Do not use phrases like 'easy to use', 'robust', 'scalable', 'fast', "
        "'various utilities', 'etc.', 'should work', 'optimized', or 'flexible'. Stick entirely to objective facts.\n"
        "3. Every instruction must be explicit. Do not say 'Install dependencies.' Say 'Run `pip install -r requirements.txt`'. "
        "If you do not see a requirements file, list the exact imports used in the scripts.\n"
        "4. Output ONLY the raw markdown content. No conversational text, intro, or markdown outer code blocks."
    )

    if readme_exists:
        print("Analyzing current README and repository files to write a defensive update...")
        system_instruction = (
            "You are a strict technical documentation auditor. Update the existing README.md file "
            "based strictly on the provided repository code context. Eliminate fluff, replace vague descriptions "
            "with precise technical definitions, and map features directly to existing files."
        ) + defensive_rules
        prompt_content = f"Existing README:\n{existing_readme_content}\n\nCurrent Repository Files:\n{project_code}"
    else:
        print("Analyzing repository files to generate a defensive README.md from scratch...")
        system_instruction = (
            "You are a strict technical documentation auditor. Generate a comprehensive, factual README.md file "
            "for this project from scratch using only the provided source code context. Include exact project purpose, "
            "file architecture, exact prerequisites derived from code imports, and precise usage instructions."
        ) + defensive_rules
        prompt_content = f"Current Repository Files:\n{project_code}"

    try:
        response = client.chat(
            model=MODEL_NAME, 
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt_content}
            ],
            options={"timeout": TIMEOUT_SECONDS}
        )
        new_readme_text = clean_markdown_block(response['message']['content'])

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_readme_text)
            
        print(f"Successfully generated defensive README.md!")
        
    except Exception as e:
        print(f"Failed to generate README via Ollama: {e}", file=sys.stderr)

def handle_git_add():
    """Checks for unstaged changes and handles adding them."""
    status = run_git_command(["git", "status", "--short"], "Failed to check git status")
    if not status:
        staged = run_git_command(["git", "diff", "--staged", "--name-only"], "Failed to check staged files")
        if staged:
            print("Using already staged changes.")
            return
        print("Everything is clean. Nothing to add, commit, or push.")
        sys.exit(0)

    print(f"\nUnstaged changes detected:\n{'-'*25}\n{status}\n{'-'*25}")
    user_choice = input("Stage all changes? (y/n) or type specific file/pattern to add: ").strip()
    
    if user_choice.lower() == 'y':
        run_git_command(["git", "add", "."], "Failed to add all files.")
        print("All changes staged.")
    elif user_choice.lower() == 'n' or user_choice == '':
        print("No files added. Proceeding with currently staged files (if any).")
    else:
        run_git_command(["git", "add", user_choice], f"Failed to add '{user_choice}'.")
        print(f"Staged: {user_choice}")

def main():
    client = Client(host=OLLAMA_HOST)

    # Step 1: Manage Documentation Feature
    handle_readme(client)

    # Step 2: Handle staging files (git add)
    handle_git_add()
    
    # Step 3: Grab the diff of what is now staged
    diff_text = run_git_command(["git", "diff", "--staged"], "Failed to get staged diff")
    if not diff_text:
        print("No staged changes detected. Aborting pipeline.")
        return

    # Step 4: AI Message Generation
    system_instruction = (
        "You are an expert git assistant. Write a concise, professional git commit message "
        "based on the provided diff. Use the Conventional Commits format (e.g., 'feat: add login', 'fix: resolve crash'). "
        "Do not include any introductory text, quotes, markdown blocks, or explanations. "
        "Output ONLY the commit message itself."
    )

    print("\nGenerating commit message via Ollama...")
    try:
        response = client.chat(
            model=MODEL_NAME, 
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Here is the git diff:\n\n{diff_text}"}
            ],
            options={"timeout": TIMEOUT_SECONDS}
        )
        commit_msg = clean_markdown_block(response['message']['content'])
    except Exception as e:
        print(f"Failed to connect to Ollama or process data: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nProposed Commit Message:\n{'-'*25}\n{commit_msg}\n{'-'*25}")

    # Step 5: Commit the changes with fallback
    user_commit = input("Apply this commit? (y/Edit/N): ").lower().strip()
    if user_commit == 'e' or user_commit == 'edit':
        commit_msg = input("Enter custom commit message: ").strip()
        if not commit_msg:
            print("Empty commit message. Aborting.")
            return
    elif user_commit != 'y':
        print("Commit aborted.")
        return
        
    run_git_command(["git", "commit", "-m", commit_msg], "Commit failed")
    print("Changes committed successfully!")

    # Step 6: Push the changes
    user_push = input("\nPush changes to remote repository? (y/N): ").lower().strip()
    if user_push == 'y':
        print("Pushing to remote...")
        run_git_command(["git", "push"], "Push failed")
        print("Successfully pushed to remote!")
    else:
        print("Push skipped. Changes remain local.")

if __name__ == "__main__":
    main()