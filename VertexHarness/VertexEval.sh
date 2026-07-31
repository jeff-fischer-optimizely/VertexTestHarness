# Vertex AI (uses existing environment variables)
# Add Python Scripts to PATH
export PATH="$PATH:/c/Users/JeFi/AppData/Local/Python/pythoncore-3.14-64/Scripts"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

harbor run \
  --dataset terminal-bench@2.0 \
  --agent claude-code \
  2>&1 | tee "${SCRIPT_DIR}/vertex_eval_output.log"
