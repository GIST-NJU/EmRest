#!/bin/bash
set -e  # Stop if any command fails

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "===== EmRest Setup Script (Conda Python 3.11) ====="
echo "[INFO] This script will create a conda env 'emrest' for EmRest and install dependencies from requirements.txt"

# Step 1: Create new Conda environment for EmRest
echo "[INFO] Creating conda environment 'emrest' with Python 3.11"
conda create -n emrest python=3.11 -y

# Step 2: Install requirements via pip
echo "[INFO] Installing EmRest dependencies..."
conda run -n emrest pip install --upgrade pip
conda run -n emrest pip install -r "$SCRIPT_DIR/requirements.txt"

# Step 3: Install spaCy model 
echo "[INFO] Installing spaCy model en_core_web_sm "

spacy_whl="lib/en_core_web_sm-3.7.1-py3-none-any.whl"
if [ -f "$spacy_whl" ]; then
    echo "Installing local spacy model 'en_core_web_sm'..."
    conda run -n emrest pip install "$spacy_whl"
    echo "Spacy model installed successfully."
else
    echo "[FAIL] Spacy wheel file '$spacy_whl' not found!"
fi

echo "===== EmRest environment setup completed successfully. ====="
