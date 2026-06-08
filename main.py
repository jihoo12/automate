import ollama
import subprocess

result = subprocess.run(["git","diff"])
# Point the client directly to the Windows host
client = ollama.Client(host='http://host.docker.internal:11434')

response = client.generate(model="gemma4", prompt=result)
print(response['response'])