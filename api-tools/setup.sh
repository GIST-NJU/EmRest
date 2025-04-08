#!/bin/bash

echo "Starting conda environments setup..."

if ! command -v conda &> /dev/null; then
    echo "[FAIL] conda command not found. Please install conda first."
    exit 1
fi

declare -A env_configs=(
    ["rl"]="3.9 ARAT-RL/requirements.txt"
    ["miner"]="3.9 MINER/requirements.txt"
    ["morest"]="3.7 morest/requirements.txt"
    ["restct"]="3.11 RestCT/requirements.txt"
    ["schemathesis"]="3.11 Schemathesis/requirements.txt"
)

for env in "${!env_configs[@]}"
do
    config=(${env_configs[$env]})
    python_version=${config[0]}
    req_file=${config[1]}

    echo "--------------------------------------"
    echo "Setting up environment: $env (Python $python_version)"

    if [ ! -f "$req_file" ]; then
        echo "[FAIL] Requirements file '$req_file' not found!"
        continue
    fi

    if conda env list | grep -qE "^$env\s"; then
        echo "Environment '$env' already exists. Skipping creation."
    else
        echo "Creating conda environment '$env' with Python $python_version..."
        conda create -y -n "$env" python="$python_version"
        echo "Environment '$env' created successfully."
    fi

    echo "Installing packages from '$req_file' into environment '$env'..."
    conda run -n "$env" pip install -r "$req_file"

    if [ "$env" = "restct" ]; then
        spacy_whl="RestCT/en_core_web_sm-3.8.0-py3-none-any.whl"
        if [ -f "$spacy_whl" ]; then
            echo "Installing local spacy model 'en_core_web_sm' into environment '$env'..."
            conda run -n "$env" pip install "$spacy_whl"
            echo "Spacy model installed successfully."
        else
            echo "[FAIL] Spacy wheel file '$spacy_whl' not found!"
        fi
    fi
    echo "Environment '$env' setup completed."
done

echo "--------------------------------------"
echo "All specified conda environments have been set up!"
