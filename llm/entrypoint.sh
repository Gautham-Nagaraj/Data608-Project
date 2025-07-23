FROM llama3.2

# sets the temperature to 1 [higher is more creative, lower is more coherent]
PARAMETER temperature 0.3

SYSTEM This is a chat between a user and a stock analyst, broker and assitant. The assistant gives helpful, detailed, and polite answers to the user’s questions based on the context.
ubuntu@ip-172-31-37-227:~/llm$ ls
Dockerfile  code_analyzer  entrypoint.sh
ubuntu@ip-172-31-37-227:~/llm$ cat entrypoint.sh
#!/bin/bash
set -e

# Start the ollama service
ollama serve &

# Wait for OLLAMA to finish booting
while ! ollama --version; do
    sleep 1
done


ollama run qwen2.5:7b

# Keep the container running
tail -f /dev/null