import ollama
import subprocess

# 1. Added capture_output=True to get the data
# 2. Added text=True to automatically decode the output to a string
result = subprocess.run(["git", "diff"], capture_output=True, text=True)

# Point the client directly to the Windows host
client = ollama.Client(host='http://host.docker.internal:11434')

# Use result.stdout to get the actual text of the diff
response = client.generate(model="gemma4", prompt=result.stdout + "\n\nwrite git commit message")
print(response['response'])