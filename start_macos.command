#!/bin/zsh

set -u

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# Finder-launched .command files may have a minimal PATH.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

find_conda() {
    if command -v conda >/dev/null 2>&1; then
        command -v conda
        return 0
    fi

    local candidates=(
        "$HOME/anaconda3/bin/conda"
        "$HOME/miniconda3/bin/conda"
        "$HOME/opt/anaconda3/bin/conda"
        "/opt/anaconda3/bin/conda"
        "/opt/anaconda3/condabin/conda"
        "/opt/homebrew/Caskroom/miniconda/base/bin/conda"
    )

    for candidate in "${candidates[@]}"; do
        if [[ -x "$candidate" ]]; then
            echo "$candidate"
            return 0
        fi
    done

    return 1
}

CONDA_EXE="$(find_conda || true)"
VENV_PYTHON="$PROJECT_ROOT/backend/.venv/bin/python"

if [[ -n "${CONDA_EXE:-}" ]]; then
    "$CONDA_EXE" run \
        -n amadeus \
        --no-capture-output \
        python "$PROJECT_ROOT/scripts/launcher.py"
else
    echo "Conda was not found. Starting the local no-AI stack instead."
    echo "This runs the WebUI, Flask, Live2D, and prerecorded reactions."
    echo "OpenRouter and GPT-SoVITS are skipped."
    echo
    if [[ ! -x "$VENV_PYTHON" ]]; then
        echo "ERROR: backend/.venv was not found."
        echo "Create it once:"
        echo
        echo "  python3.12 -m venv backend/.venv"
        echo "  backend/.venv/bin/pip install -r backend/requirements-no-ai.txt"
        echo
        echo "Or install Anaconda/Miniconda and use the full stack."
        echo
        read "?Press Enter to close..."
        exit 1
    fi
    "$VENV_PYTHON" "$PROJECT_ROOT/scripts/launcher.py" --no-ai
fi

EXIT_CODE=$?

if [[ $EXIT_CODE -ne 0 ]]; then
    echo
    echo "Maho Overlay launcher exited with an error."
    echo "Check .runtime/logs for service logs."
    read "?Press Enter to close..."
fi

exit $EXIT_CODE
