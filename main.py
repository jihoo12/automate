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

def handle_git_add():
    """Checks for unstaged changes and handles adding them."""
    # Check what's modified/untracked
    status = run_git_command(["git", "status", "--short"], "Failed to check git status")
    
    if not status:
        # Check if anything is already staged from a previous manual add
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
        # User typed a specific file path or wildcard pattern
        run_git_command(["git", "add", user_choice], f"Failed to add '{user_choice}'. Make sure the path is correct.")
        print(f"Staged: {user_choice}")

def main():
    # Step 1: Handle staging files (git add)
    handle_git_add()
    
    # Step 2: Grab the diff of what is now staged
    diff_text = run_git_command(["git", "diff", "--staged"], "Failed to get staged diff")
    
    if not diff_text:
        print("No staged changes detected. Aborting pipeline.")
        return

    # Step 3: AI Message Generation
    system_instruction = (
        "You are an expert git assistant. Write a concise, professional git commit message "
        "based on the provided diff. Use the Conventional Commits format (e.g., 'feat: add login', 'fix: resolve crash'). "
        "Do not include any introductory text, quotes, markdown blocks, or explanations. "
        "Output ONLY the commit message itself."
    )

    print("\nGenerating commit message via Ollama...")
    try:
        client = Client(host='http://host.docker.internal:11434')
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

    # Step 4: Commit the changes
    user_commit = input("Apply this commit? (y/N): ").lower()
    if user_commit != 'y':
        print("Commit aborted.")
        return
        
    run_git_command(["git", "commit", "-m", commit_msg], "Commit failed (check hooks or linters)")
    print("Changes committed successfully!")

    # Step 5: Push the changes
    user_push = input("\nPush changes to remote repository? (y/N): ").lower()
    if user_push == 'y':
        print("Pushing to remote...")
        # Runs a standard 'git push'. If you need to track a new branch, 
        # it will output Git's native upstream error message instructions.
        run_git_command(["git", "push"], "Push failed")
        print("Successfully pushed to remote!")
    else:
        print("Push skipped. Changes remain local.")

if __name__ == "__main__":
    main()