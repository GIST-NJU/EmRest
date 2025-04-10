#!/bin/bash

set -e  # Stop the script immediately if any error occurs

echo "===== Installing Poetry ====="

# 1. Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "[FAIL] Python 3 not found. Please install Python 3 first."
    exit 1
fi

# 2. Check if Poetry is already installed
if command -v poetry &> /dev/null; then
    echo "[ OK ] Poetry is already installed: $(poetry --version)"
else
    echo "Installing Poetry..."

    # Use the official installer script
    # For details: https://python-poetry.org/docs/#installation
    curl -sSL https://install.python-poetry.org | python3 -

    # Poetry is typically installed into ~/.local/bin/poetry by default
    POETRY_BIN="$HOME/.local/bin"

    # 3. Ensure that ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$POETRY_BIN:"* ]]; then
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$HOME/.bashrc"
        echo "[ OK ] Added '\$HOME/.local/bin' to PATH in .bashrc"
        # Load .bashrc so the change is immediately effective in the current session
        source "$HOME/.bashrc"
    fi

    echo "[ OK ] Poetry installed: $(poetry --version)"
fi

echo "===== Poetry installation finished. ====="
