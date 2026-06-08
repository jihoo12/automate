import os
import sys
import subprocess
from ollama import Client

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

def get_project_context():
    """Reads project text files to give the AI context for writing/updating README."""
    context = ""
    # Look for common code files to explain, avoiding large binary/ignored directories
    ignored_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', 'env'}
    allowed_extensions = {'.py', '.js', '.ts', '.go', '.rs', '.json', '.sh', '.yml', '.yaml', '.txt'}
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for file in files:
            _, ext = os.path.splitext(file)
            if ext in allowed_extensions:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        context += f"\n--- File: {file_path} ---\n{f.read()[:2000]}\n" # Limit size per file
                except Exception:
                    pass
    return context

def handle_readme(client):
    """Asks the user if they want to create/update the README using AI context."""
    user_choice = input("\nDo you want to generate or update README.md? (y/N): ").lower()
    if user_choice != 'y':
        return

    readme_path = "README.md"
    readme_exists = os.path.exists(readme_path)
    
    # Read existing content if it exists
    existing_readme_content = ""
    if readme_exists:
        with open(readme_path, 'r', encoding='utf-8') as f:
            existing_readme_content = f.read()

    project_code = get_project_context()

    if readme_exists:
        print("Analyzing current README and repository files to write an update...")
        system_instruction = (
            "You are a technical documentation assistant. Update the existing README.md file "
            "based on the provided repository code context. Improve formatting, explain any new structures, "
            "and fix omissions. Output ONLY the raw markdown content of the new README.md. No notes or markdown wrappers."
        )
        prompt_content = f"Existing README:\n{existing_readme_content}\n\nCurrent Repository Files:\n{project_code}"
    else:
        print("Analyzing repository files to generate a new README.md...")
        system_instruction = (
            "You are a technical documentation assistant. Generate a professional, comprehensive README.md file "
            "for this project from scratch using the provided source code context. Include project purpose, architecture, "
            "prerequisites, usage instructions, and clean markdown layouts. Output ONLY the raw markdown content. No conversational text."
        )
        prompt_content = f"Current Repository Files:\n{project_code}"

    try:
        response = client.chat(
            model="gemma4", 
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt_content}
            ]
        )
        new_readme_text = response['message']['content'].strip()
        
        # Clean markdown code block wraps if the AI accidentally added them
        if new_readme_text.startswith("```markdown"):
            new_readme_text = new_readme_text[11:-3].strip()
        elif new_readme_text.startswith("```"):
            new_readme_text = new_readme_text[3:-3].strip()

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_readme_text)
            
        print(f"Successfully {'updated' if readme_exists else 'created'} README.md!")
        
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
    # Setup Ollama Client
    client = Client(host='http://host.docker.internal:11434')

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
            model="gemma4", 
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Here is the git diff:\n\n{diff_text}"}
            ]
        )
        commit_msg = response['message']['content'].strip()
    except Exception as e:
        print(f"Failed to connect to Ollama: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nProposed Commit Message:\n{'-'*25}\n{commit_msg}\n{'-'*25}")

    # Step 5: Commit the changes
    user_commit = input("Apply this commit? (y/N): ").lower()
    if user_commit != 'y':
        print("Commit aborted.")
        return
        
    run_git_command(["git", "commit", "-m", commit_msg], "Commit failed")
    print("Changes committed successfully!")

    # Step 6: Push the changes
    user_push = input("\nPush changes to remote repository? (y/N): ").lower()
    if user_push == 'y':
        print("Pushing to remote...")
        run_git_command(["git", "push"], "Push failed")
        print("Successfully pushed to remote!")
    else:
        print("Push skipped. Changes remain local.")

if __name__ == "__main__":
    main()