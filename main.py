import sys
import subprocess
from ollama import Client

def get_git_diff():
    try:
        result = subprocess.run(
            ["git", "diff", "--staged"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'git' command not found. Is it installed?", file=sys.stderr)
        sys.exit(1)

def main():
    diff_text = get_git_diff()
    
    if not diff_text:
        print("No staged changes detected. Use 'git add' first.")
        return

    system_instruction = (
        "You are an expert git assistant. Write a concise, professional git commit message "
        "based on the provided diff. Use the Conventional Commits format (e.g., 'feat: add login', 'fix: resolve crash'). "
        "Do not include any introductory text, quotes, markdown blocks, or explanations. "
        "Output ONLY the commit message itself."
    )

    try:
        client = Client(host='http://host.docker.internal:11434')
        response = client.chat(
            model="gemma4", 
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Here is the git diff:\n\n{diff_text}"}
            ]
        )
        
        # Pull the message out inside the try block where 'response' safely exists
        commit_msg = response['message']['content'].strip()
        
    except Exception as e:
        print(f"Failed to connect to Ollama: {e}", file=sys.stderr)
        # Exit early so the script doesn't attempt to use a non-existent commit message
        sys.exit(1)

    # Now this is perfectly safe to run
    print(f"\nProposed Commit Message:\n{'-'*25}\n{commit_msg}\n{'-'*25}")

    user_input = input("Apply this commit? (y/N): ").lower()
    if user_input == 'y':
        # Added check=True here too, just in case the commit fails (e.g., pre-commit hooks)
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print("Changes committed successfully!")
    else:
        print("Commit aborted.")

if __name__ == "__main__":
    main()