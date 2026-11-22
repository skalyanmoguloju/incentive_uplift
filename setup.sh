#!/bin/bash

set -e

# Setup the current project directory
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# Locations for brew profiles
BREW_PATH="/opt/homebrew/bin/brew"
ZPROFILE="$HOME/.zprofile"

# Setup for brew if the system does not have it installed
if ! command -v brew >/dev/null 2>&1; then
    if [ ! -x "$BREW_PATH" ]; then
        echo "Homebrew is not available. Installing it..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    if [ -x "$BREW_PATH" ]; then
        if ! grep -qF 'eval "$(/opt/homebrew/bin/brew shellenv)"' "$ZPROFILE" 2>/dev/null; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$ZPROFILE"
        fi

        eval "$("$BREW_PATH" shellenv)"
    fi
fi


if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew setup failed."
    exit 1
fi

# Installing python
brew install python@3.11
brew install libomp

PYTHON_BIN="$(brew --prefix python@3.11)/bin/python3.11"

if [ ! -x "$PYTHON_BIN" ]; then
    echo "Python 3.11 was not found."
    exit 1
fi

if [ ! -d ".venv" ]; then
    "$PYTHON_BIN" -m venv .venv
fi

# Activating the virtual environment
source .venv/bin/activate

python -m pip install --upgrade pip

# Installing the defined libraries needed for this peoject
python -m pip install -r requirements.txt


echo "Setup completed."
python --version


# Setup validation
echo "Validating installed libraries..."

python - <<'PY'
import numpy
import pandas
import scipy
import sklearn
import matplotlib
import seaborn
import lightgbm
import torch

print("All core libraries imported successfully")
print("PyTorch:", torch.__version__)
print("MPS available:", torch.backends.mps.is_available())
PY