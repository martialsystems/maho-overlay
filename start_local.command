#!/bin/zsh

set -u

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# Finder-launched .command files may have a minimal PATH.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

VENV_PYTHON="$PROJECT_ROOT/backend/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "ERROR: backend/.venv was not found."
    echo "Create it once:"
    echo
    echo "  python3.12 -m venv backend/.venv"
    echo "  backend/.venv/bin/pip install -r backend/requirements-no-ai.txt"
    echo
    read "?Press Enter to close..."
    exit 1
fi

"$VENV_PYTHON" "$PROJECT_ROOT/scripts/launcher.py" --no-ai

EXIT_CODE=$?

if [[ $EXIT_CODE -ne 0 ]]; then
    echo
    echo "Maho Overlay launcher exited with an error."
    echo "Check .runtime/logs for service logs."
    read "?Press Enter to close..."
fi

exit $EXIT_CODE
